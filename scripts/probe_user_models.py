import vertexai
from vertexai.generative_models import GenerativeModel
import os

PROJECT_ID = "prompt-wars-bengaluru-2026"
LOCATION   = "us-central1"

print(f"Probing {PROJECT_ID} for specific Hackathon models in {LOCATION}...", flush=True)
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Probing user suggested models + common fallbacks
CANDIDATES = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.1-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

for model_id in CANDIDATES:
    try:
        model = GenerativeModel(model_id)
        # Using a very small request
        response = model.generate_content("ping", generation_config={"max_output_tokens": 1})
        print(f"  [OK] {model_id}", flush=True)
    except Exception as e:
        err = str(e).split('\n')[0]
        print(f"  [FAIL] {model_id}: {err[:100]}", flush=True)

print("\nProbe done.", flush=True)
