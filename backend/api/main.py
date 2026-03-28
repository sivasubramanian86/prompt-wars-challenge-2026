"""
FastAPI application — Omni-Bridge Core Orchestrator.

Routes:
  GET  /health                  → liveness probe (Cloud Run)
  POST /v1/incident/ingest      → multipart form: text (str) + audio (file, optional)
  POST /v1/incident/ingest-gcs  → JSON body: {"gcs_uri": "gs://bucket/file.ext"}
  GET  /v1/samples              → list available GCS sample URIs
  GET  /                        → serves frontend/index.html
"""

import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.agents.pipeline import OmniBridgePipeline
from backend.schemas.incident import IncidentExecutionPayload

# ── Structured JSON logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# ── Pipeline singleton ─────────────────────────────────────────────────────────
pipeline = OmniBridgePipeline()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Omni-Bridge Orchestrator starting up.")
    yield
    logger.info("Omni-Bridge Orchestrator shutting down.")


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Omni-Bridge Core Orchestrator",
    description="Multi-modal crisis data synthesis → deterministic JSON execution payload.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to known origins in production
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Health check (Cloud Run liveness probe) ────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "service": "omni-bridge-orchestrator", "version": "1.0.0"}


# ── Core inference endpoint ────────────────────────────────────────────────────
@app.post(
    "/v1/incident/ingest",
    response_model=IncidentExecutionPayload,
    tags=["orchestration"],
    summary="Ingest unstructured incident data and synthesize an execution payload.",
)
async def ingest_incident(
    request: Request,
    text: str | None = Form(None, description="Raw text or voice transcript"),
    audio: UploadFile | None = File(None, description="Audio file (wav/webm/mp3/ogg)"),
):
    start = time.monotonic()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    logger.info(
        json.dumps(
            {
                "event": "ingest_start",
                "request_id": request_id,
                "has_text": bool(text),
                "has_audio": bool(audio),
            }
        )
    )

    audio_bytes: bytes | None = None
    audio_mime = "audio/webm"
    if audio:
        audio_bytes = await audio.read()
        audio_mime = audio.content_type or "audio/webm"

    try:
        payload = await pipeline.run(
            text_input=text,
            audio_bytes=audio_bytes,
            audio_mime=audio_mime,
        )
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as exc:
        logger.error(
            json.dumps({"event": "ingest_error", "request_id": request_id, "error": str(exc)})
        )
        raise HTTPException(status_code=500, detail="Pipeline execution failed.")

    latency_ms = round((time.monotonic() - start) * 1000, 2)
    logger.info(
        json.dumps(
            {
                "event": "ingest_complete",
                "request_id": request_id,
                "incident_id": str(payload.incident_id),
                "domain": payload.domain_classification.value,
                "urgency": payload.urgency_level.value,
                "verification": payload.verification_flag.value,
                "latency_ms": latency_ms,
            }
        )
    )
    return payload


# ── GCS ingest endpoint ───────────────────────────────────────────────────────────────
from pydantic import BaseModel as _BM


class GCSIngestRequest(_BM):
    gcs_uri: str


@app.post(
    "/v1/incident/ingest-gcs",
    response_model=IncidentExecutionPayload,
    tags=["orchestration"],
    summary="Ingest an incident directly from a GCS object URI (text, image, or audio).",
)
async def ingest_from_gcs(request: Request, body: GCSIngestRequest):
    start = time.monotonic()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    gcs_uri = body.gcs_uri.strip()

    if not gcs_uri.startswith("gs://"):
        raise HTTPException(status_code=422, detail="gcs_uri must start with gs://")

    logger.info(json.dumps({"event": "gcs_ingest_start", "request_id": request_id, "uri": gcs_uri}))

    try:
        payload = await pipeline.run_from_gcs(gcs_uri)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as exc:
        logger.error(json.dumps({"event": "gcs_ingest_error", "uri": gcs_uri, "error": str(exc)}))
        raise HTTPException(status_code=500, detail=f"GCS pipeline failed: {exc}")

    latency_ms = round((time.monotonic() - start) * 1000, 2)
    logger.info(json.dumps({
        "event": "gcs_ingest_complete",
        "request_id": request_id,
        "incident_id": str(payload.incident_id),
        "latency_ms": latency_ms,
    }))
    return payload


# ── Sample catalogue ───────────────────────────────────────────────────────────────
GCS_BUCKET = "omnibridge-samples-pwb2026"
SAMPLE_FILES = [
    {"uri": f"gs://{GCS_BUCKET}/samples/01_medical_er_voice_transcript.txt",  "label": "Medical ER — Voice Transcript",     "type": "text",  "domain": "Medical"},
    {"uri": f"gs://{GCS_BUCKET}/samples/02_traffic_accident_radio_log.txt",   "label": "Traffic — Radio Log (Garbled)",      "type": "text",  "domain": "Traffic"},
    {"uri": f"gs://{GCS_BUCKET}/samples/03_hazmat_crisis_field_report.txt",   "label": "Crisis — Hazmat Field Report",       "type": "text",  "domain": "Crisis_Response"},
    {"uri": f"gs://{GCS_BUCKET}/samples/04_weather_flood_email_chain.txt",    "label": "Weather — Flood Email Chain",        "type": "text",  "domain": "Weather"},
    {"uri": f"gs://{GCS_BUCKET}/samples/05_whatsapp_fire_crisis_chat.txt",    "label": "Crisis — WhatsApp Chat Log",         "type": "text",  "domain": "Crisis_Response"},
    {"uri": f"gs://{GCS_BUCKET}/messy_medical_form.png",                      "label": "Image — Messy Medical Triage Form",  "type": "image", "domain": "Medical"},
    {"uri": f"gs://{GCS_BUCKET}/traffic_accident_scene.png",                  "label": "Image — Traffic Accident (Dashcam)", "type": "image", "domain": "Traffic"},
    {"uri": f"gs://{GCS_BUCKET}/hazmat_control_room.png",                     "label": "Image — Hazmat Control Room",        "type": "image", "domain": "Crisis_Response"},
]


@app.get("/v1/samples", tags=["orchestration"], summary="List available GCS sample incident files.")
async def list_samples():
    return {"bucket": GCS_BUCKET, "samples": SAMPLE_FILES}


# ── Frontend static serving ────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")


@app.get("/", include_in_schema=False)
async def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        return JSONResponse({"status": "ok", "note": "Frontend not bundled in this image."})
    return FileResponse(index_path)


if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")
