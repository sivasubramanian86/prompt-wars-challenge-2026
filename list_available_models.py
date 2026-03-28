"""
list_available_models.py
Probes all common Vertex AI Gemini model IDs and reports which ones
are callable in this project/region. Requires ADC to be configured.

Usage:
    pip install google-cloud-aiplatform
    gcloud auth application-default login
    python list_available_models.py
"""

import sys
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "prompt-wars-bengaluru-2026"
LOCATIONS  = ["us-central1", "us-east4", "us-west1", "europe-west1", "asia-southeast1"]

CANDIDATE_MODELS = [
    # Gemini 2.0 Flash
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
    # Gemini 2.5
    "gemini-2.5-flash-preview-04-17",
    "gemini-2.5-pro-preview-03-25",
    # Gemini 1.5 Flash
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash-8b-001",
    # Gemini 1.5 Pro
    "gemini-1.5-pro",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro-002",
]

PING_PROMPT = "Reply with one word: OK"

print(f"\nProbing project: {PROJECT_ID}")
print("=" * 70)

results = {}

for location in LOCATIONS:
    print(f"\n--- Location: {location} ---")
    vertexai.init(project=PROJECT_ID, location=location)
    for model_id in CANDIDATE_MODELS:
        try:
            model    = GenerativeModel(model_id)
            response = model.generate_content(PING_PROMPT)
            status   = "AVAILABLE"
            note     = response.text.strip()[:30]
        except Exception as e:
            err = str(e)
            if "404" in err or "not found" in err.lower():
                status = "NOT_FOUND"
            elif "403" in err or "permission" in err.lower():
                status = "PERMISSION_DENIED"
            elif "429" in err or "quota" in err.lower():
                status = "QUOTA_EXCEEDED"
            else:
                status = "ERROR"
            note = err[:60]

        tag = "OK" if status == "AVAILABLE" else "  "
        print(f"  [{tag}] {model_id:<45} → {status}  {note}")
        results[(location, model_id)] = status

print("\n" + "=" * 70)
print("SUMMARY — AVAILABLE models:")
for (loc, mid), st in results.items():
    if st == "AVAILABLE":
        print(f"  {loc}  /  {mid}")

print("\nDone.")
