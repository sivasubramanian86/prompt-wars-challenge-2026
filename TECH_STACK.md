# Omni-Bridge Technology Stack

This project is built using modern, production-grade cloud-native technologies optimized for zero-latency AI orchestration.

## 1. Core Runtime & Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI (Asynchronous, High-Performance)
- **Validation**: Pydantic v2 (Strict Schema Enforcement)
- **Settings**: Pydantic-Settings (Environment-driven configuration)

## 2. Artificial Intelligence (Agent Mesh)
- **Platform**: **Google Cloud Vertex AI**
- **Foundation Models**:
  - **Gemini 2.5 Flash**: Primary model for high-reasoning synthesis and specialized domain extraction.
  - **Gemini 2.5 Flash Lite**: Optimized, low-latency model for initial triage and audio transcription.
- **Multimodal capabilities**: Native support for Text, Image (GCS URI), and Audio (GCS/Local).
- **Design Pattern**: Autonomous Sequential Agent Mesh (Custom Orchestration).

## 3. Cloud Infrastructure (GCP)
- **Compute**: 
  - **Google Cloud Run** (Containerized Serverless)
  - **Google Kubernetes Engine (GKE)** (High-Availability scaling)
- **Messaging**: **Cloud Pub/Sub** (Asynchronous Human-in-the-Loop escalation)
- **Storage**: **Google Cloud Storage (GCS)** & **Firestore (Memory Module)**
  - GCS-Native Ingestion: `gs://` URIs ingested directly via Vertex AI `Part.from_uri`.
  - Sample Incident Catalogue: Pre-populated synthetic logs and multimodal data.
- **Authentication**: 
  - Google Identity Services (SSO UI Auth).
  - Application Default Credentials (ADC) for backend.
- **Analytics**: **Google Analytics (gtag.js)**

## 4. Frontend & Command Centers
- **Primary Orchestrator UI**: Single-Page Application (SPA).
  - Vanilla CSS (Custom Glassmorphism Design System).
  - Vanilla Javascript (Functional-reactive pattern).
  - UI Components: Real-time AI Insights, Pipeline Tracker, GCS Sample Discovery.
- **HITL Dashboard**: **Streamlit Web Application**
  - Consumes from Pub/Sub via subscription.
  - Interactive Python-based dashboard for human verification.

## 5. DevSecOps & QA
- **Version Control**: Git (GitHub)
- **Testing**: Pytest & Pytest-Asyncio (Integration & Smoke testing)
- **Containerization**: 2-stage Production Dockerfile (Non-root user).
- **Security**: 
  - Automated PII stripping from logs.
  - Zero-storage of API keys (managed via IAM).
  - `SECURITY.md` disclosure policy.
