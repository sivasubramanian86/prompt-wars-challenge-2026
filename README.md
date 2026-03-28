# Omni-Bridge Core Orchestrator

**Prompt Wars Bengaluru 2026 — Hackathon Submission**

Zero-latency multi-modal crisis data synthesis engine. Converts unstructured incident input (text, voice, sensor data) into verified, deterministic JSON execution payloads via a 5-step agent pipeline on Google Vertex AI.

---

## Architecture

```
[Text / Audio Input]
        │
   POST /v1/incident/ingest
        │
┌───────▼─────────────────────────────────────────┐
│         Omni-Bridge Pipeline (Vertex AI)        │
│                                                 │
│  Step 1: Modality Triage + Intent/Urgency       │
│  Step 2: Domain Specialist Routing              │
│          ├── Medical_Triage_Agent               │
│          ├── Civic_Emergency_Agent              │
│          └── Logistics_Routing_Agent            │
│  Step 3: Verification & Grounding (rule-based)  │
│  Step 4: Action Synthesis → JSON Payload        │
└───────┬──────────────────────────┬──────────────┘
        │                          │
   JSON Response          Cloud Pub/Sub (HITL)
                          omnibridge-hitl-queue
```

## Stack

- **Runtime**: Python 3.12 + FastAPI + Uvicorn
- **AI**: Google Vertex AI (Gemini 2.0 Flash)
- **Infrastructure**: GCP Cloud Run + Cloud Pub/Sub
- **Auth**: Application Default Credentials (no API keys)
- **Frontend**: Vanilla HTML/CSS/JS — command-center dark UI

## Local Development

```bash
# 1. Authenticate with GCP
gcloud auth application-default login

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure env
cp .env.example .env

# 4. Run
uvicorn backend.api.main:app --reload --port 8080
```

Open `http://localhost:8080` for the frontend UI.

## Deploy to Cloud Run

```bash
# One-time GCP setup (run once)
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

## API

### POST /v1/incident/ingest

Accepts `multipart/form-data`:

| Field   | Type   | Required | Description                     |
|---------|--------|----------|---------------------------------|
| `text`  | string | Optional | Raw incident text or transcript |
| `audio` | file   | Optional | Audio file (webm, wav, mp3)     |

At least one of `text` or `audio` must be provided.

**Response**: `IncidentExecutionPayload` JSON schema.

### GET /health

Returns `{"status": "ok"}` — used by Cloud Run liveness probe.

## Security Notes

- No API keys in code. Auth via Cloud Run Service Account + ADC.
- Verification flag is deterministic (rule engine), never LLM-decided.
- PII never logged — only `incident_id`, `domain`, `latency_ms`.
- HITL incidents published to Cloud Pub/Sub, never silently dropped.
