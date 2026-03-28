# Security Policy

## Overview

Omni-Bridge Core Orchestrator is a multi-modal crisis data synthesis system built for
**Prompt Wars Bengaluru 2026**. Because this system processes emergency incident data,
security and privacy are treated as first-class concerns.

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` branch (latest) | Active |
| Any prior tagged release | Best-effort only |

---

## Reporting a Vulnerability

**Do not file a public GitHub Issue for security vulnerabilities.**

Report security issues privately via email:

**kailasamsiva@gmail.com** — Subject: `[SECURITY] Omni-Bridge <brief description>`

Include:
- Description of the vulnerability
- Reproduction steps or proof-of-concept
- Impact assessment (data exposure, privilege escalation, denial of service, etc.)
- Suggested fix if known

We will acknowledge within **48 hours** and aim to ship a fix within **7 days** for
critical findings.

---

## Security Architecture

### 1. Authentication & IAM (Least Privilege)

- Cloud Run service runs under a **dedicated Service Account** (`omnibridge-sa`)
  with only the roles it needs:
  - `roles/aiplatform.user` — Vertex AI Gemini inference
  - `roles/pubsub.publisher` — HITL queue publishing
  - `roles/storage.objectViewer` — read-only access to sample bucket
- No `roles/editor` or `roles/owner` granted to the service identity
- **No API keys in code or environment variables.** Authentication uses
  Google Application Default Credentials (ADC) via Cloud Run's metadata server

### 2. Secret Management

- No secrets are hardcoded in source. `.env` files are excluded by `.gitignore`
- Production configuration relies solely on GCP-native ADC; no service account
  JSON key files are used or stored
- For local development, credentials are obtained via `gcloud auth application-default login`

### 3. Data Handling & PII

- **Incident text is never logged.** The logging middleware records only:
  `incident_id`, `domain`, `urgency_level`, `verification_flag`, `latency_ms`
- Audio bytes uploaded by users are processed in-memory and never persisted to disk
- GCS sample files contain **synthetic/fictional incident data only** — no real PII
- Cloud Pub/Sub HITL messages contain the structured `IncidentExecutionPayload` JSON;
  raw user input is never republished

### 4. Input Validation

- All API inputs are validated via **Pydantic v2 schemas** with strict type enforcement
- GCS URIs are validated to start with `gs://` before any GCS client calls
- File uploads are size-limited by FastAPI's default multipart parser
- Downstream mock API payloads are schema-validated before dispatch

### 5. Transport Security

- All traffic is served over **HTTPS** via Cloud Run's managed TLS
- CORS is currently set to `*` (open for hackathon demo purposes)
  — restrict to known origins before any production deployment

### 6. Container Hardening

- Docker image uses a **non-root user** (`appuser`, UID 1000)
- Multi-stage build — only runtime dependencies in the final image
- No shell, no package manager, no build tools in the production layer

---

## Known Limitations (Hackathon Scope)

The following are acknowledged trade-offs accepted for the hackathon time constraint:

| Item | Limitation | Production Fix |
|------|-----------|---------------|
| CORS | `allow_origins=["*"]` | Restrict to known frontend origins |
| Rate limiting | None implemented | Add Cloud Armor or FastAPI middleware |
| Audio file size | No hard cap set | Enforce `MAX_UPLOAD_BYTES` in middleware |
| HITL payload | Full payload published; no field-level redaction | Strip PII fields before Pub/Sub publish |
| GCS bucket | Uniform bucket-level access; no object-level ACL | Implement CMEK + object-level encryption |

---

## Dependency Updates

Dependencies are pinned in `requirements.txt`. Review and update regularly using:

```bash
pip list --outdated
pip-audit  # scan for known CVEs
```
