# Omni-Bridge Core Orchestrator

**Prompt Wars Bengaluru 2026 — Hackathon Submission**

> Zero-latency multi-modal crisis orchestration. Converts unstructured incident data — voice transcripts, scanned forms, dashcam images, sensor dumps, WhatsApp chats — into verified, deterministic JSON execution payloads via a 5-step Vertex AI agent pipeline.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Live-green)](https://omni-bridge-orchestrator-448512759847.us-central1.run.app)
[![Vertex AI](https://img.shields.io/badge/Powered%20by-Vertex%20AI%20Gemini%202.5-blueviolet)](https://cloud.google.com/vertex-ai)

**Live URL:** `https://omni-bridge-orchestrator-448512759847.us-central1.run.app`

---

## The Problem

Emergency response systems fail at the boundary between human chaos and machine precision. A paramedic's frantic radio call, a blurry dashcam photo, a WhatsApp group panic thread — none of these feed cleanly into CAD systems, EHR APIs, or civil defense dispatch. The gap between unstructured crisis data and structured, actionable output costs lives.

---

## The Solution

Omni-Bridge bridges that gap deterministically. It ingests **any modality** of messy incident data and outputs a **schema-validated, rule-verified JSON execution payload** — ready for downstream systems.

**Anti-hallucination guarantee:** The verification gate is rule-based (not LLM-decided). If critical fields are missing or confidence falls below threshold, the incident is automatically escalated to a human operator via Cloud Pub/Sub — never silently dropped.

---

## Architecture

```
[Text / Audio / Image / GCS URI]
             │
     POST /v1/incident/ingest
     POST /v1/incident/ingest-gcs
             │
┌────────────▼────────────────────────────────────────┐
│          Omni-Bridge Pipeline (Vertex AI)           │
│           Powered by Gemini 2.5 Flash               │
│                                                     │
│  Step 1: Modality Triage + Intent/Urgency           │
│          (Gemini 2.5-flash-lite)                    │
│          ├── Text → direct                          │
│          ├── Audio → transcription pipeline         │
│          └── Image → Part.from_uri                  │
│                                                     │
│  Step 2: Domain Specialist Routing                  │
│          (Gemini 2.5-flash)                         │
│          ├── Civic_Emergency_Agent (Traffic)        │
│          ├── Civic_Emergency_Agent (Weather/Crisis) │
│          └── General_Triage_Agent                   │
│                                                     │
│  Step 3: Verification & Grounding (DETERMINISTIC)   │
│          Rule engine — not LLM-decided              │
│          Checks: dosages, GPS, patient IDs          │
│                                                     │
│  Step 4: Action Synthesis → IncidentExecutionPayload│
└────┬────────────────────────────┬───────────────────┘
     │                            │
 JSON Response          Cloud Pub/Sub HITL
                        omnibridge-hitl-queue
                        (if verification fails)
```

---

## Input Modalities

| Modality | Endpoint | Description |
|----------|----------|-------------|
| Raw text / transcript | `POST /v1/incident/ingest` | Form field `text` |
| Audio file | `POST /v1/incident/ingest` | Form field `audio` (wav/webm/mp3/ogg/flac) |
| GCS text file | `POST /v1/incident/ingest-gcs` | JSON `{"gcs_uri": "gs://bucket/file.txt"}` |
| GCS audio file | `POST /v1/incident/ingest-gcs` | JSON `{"gcs_uri": "gs://bucket/file.wav"}` |
| GCS image file | `POST /v1/incident/ingest-gcs` | JSON `{"gcs_uri": "gs://bucket/photo.png"}` |

---

## Sample Incident Data

Pre-loaded synthetic samples in `gs://omnibridge-samples-pwb2026/`:

| File | Scenario | Domain |
|------|----------|--------|
| `samples/01_medical_er_voice_transcript.txt` | ER doctor voice call — STEMI, garbled details | Medical |
| `samples/02_traffic_accident_radio_log.txt` | Unit 7 radio log — NH-44 pile-up, fuel spill | Traffic |
| `samples/03_hazmat_crisis_field_report.txt` | Peenya industrial ammonia leak, incomplete form | Crisis_Response |
| `samples/04_weather_flood_email_chain.txt` | BBMP flood email chain — conflicting info | Weather |
| `samples/05_whatsapp_fire_crisis_chat.txt` | Koramangala WhatsApp group — warehouse fire | Crisis_Response |
| `messy_medical_form.png` | Scanned handwritten triage form (AI-generated) | Medical |
| `traffic_accident_scene.png` | Rainy night dashcam pile-up (AI-generated) | Traffic |
| `hazmat_control_room.png` | Industrial control room during ammonia alert (AI-generated) | Crisis_Response |

All samples are accessible one-click via the **GCS Samples** tab in the UI.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Google Vertex AI — Gemini 2.0 Flash |
| Backend | FastAPI + Pydantic v2 (stateless) |
| Runtime | Python 3.12 + Uvicorn |
| Infra | GCP Cloud Run (auto-scaling, HTTPS) |
| HITL | Google Cloud Pub/Sub (`omnibridge-hitl-queue`) |
| Auth | GCP Application Default Credentials (no API keys) |
| Frontend | Vanilla HTML/CSS/JS — glassmorphism command-center UI |
| Container | Multi-stage Docker, non-root user |

---

## API Reference

### `POST /v1/incident/ingest`
Multipart form-data.

| Field | Type | Required |
|-------|------|----------|
| `text` | string | Optional |
| `audio` | file | Optional |

At least one field required.

### `POST /v1/incident/ingest-gcs`
JSON body.

```json
{ "gcs_uri": "gs://omnibridge-samples-pwb2026/samples/01_medical_er_voice_transcript.txt" }
```

### `GET /v1/samples`
Returns the full sample catalogue with URIs, labels, types, and expected domains.

### `GET /health`
Liveness probe — returns `{"status": "ok", "service": "omni-bridge-orchestrator", "version": "1.0.0"}`.

---

## Response Schema — `IncidentExecutionPayload`

```json
{
  "incident_id": "uuid4",
  "domain_classification": "Medical | Traffic | Weather | Crisis_Response | General",
  "urgency_level": "CRITICAL | HIGH | MODERATE | LOW",
  "synthesized_context": "Two-sentence factual summary.",
  "extracted_entities": {
    "key_variables": ["entity1", "entity2"],
    "missing_critical_data": ["medication_dosage_not_confirmed"]
  },
  "verification_flag": "PASS | FAIL | REQUIRES_HUMAN_IN-THE-LOOP",
  "execution_payload": {
    "target_system": "Hospital_EHR_System",
    "action_command": "dispatch_medical_response",
    "parameters": {}
  }
}
```

**`verification_flag` is always set by a deterministic rule engine, never by the LLM.**

---

## Local Development

```bash
# 1. Authenticate
gcloud auth application-default login

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env — GCP_PROJECT_ID, GCP_LOCATION, etc.

# 4. Run
uvicorn backend.api.main:app --reload --port 8080
```

Open `http://localhost:8080`.

---

## Deploy to Cloud Run

```bash
# One-time setup (APIs, Pub/Sub, IAM)
bash setup_gcp.sh

# Deploy
gcloud run deploy omni-bridge-orchestrator \
  --source . \
  --project prompt-wars-bengaluru-2026 \
  --region us-central1 \
  --service-account omnibridge-sa@prompt-wars-bengaluru-2026.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --quiet
```

---

## Security

See [SECURITY.md](SECURITY.md) for the full security policy, including IAM design,
PII handling, container hardening, and responsible disclosure contacts.

---

## Project Structure

```
.
├── backend/
│   ├── agents/
│   │   └── pipeline.py        # 5-step Vertex AI pipeline
│   ├── api/
│   │   └── main.py            # FastAPI routes
│   ├── schemas/
│   │   └── incident.py        # Pydantic v2 output contract
│   └── tools/
│       ├── gcs_ingest.py      # GCS URI resolver (text/audio/image)
│       └── mock_apis.py       # Downstream API stubs
├── frontend/
│   ├── index.html             # Single-page command-center UI
│   ├── style.css              # Glassmorphism dark theme
│   └── app.js                 # Audio recorder, GCS tab, JSON viewer
├── samples/                   # Synthetic messy incident data
├── Dockerfile                 # Multi-stage, non-root production image
├── setup_gcp.sh               # One-time GCP infra setup script
├── requirements.txt
├── LICENSE
└── SECURITY.md
```

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

*Built for Prompt Wars Bengaluru 2026 by Siva Subramanian.*
