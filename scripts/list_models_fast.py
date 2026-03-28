"""
list_models_v3.py
Optimized model list for prompt-wars-bengaluru-2026.
Uses flush=True for immediate feedback.
"""
import vertexai
from vertexai.generative_models import GenerativeModel
import os

PROJECT_ID = "prompt-wars-bengaluru-2026"
LOCATION   = "us-central1"

CANDIDATES = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-pro",
    "gemini-1.5-pro-001",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
]

print(f"Probing {PROJECT_ID} in {LOCATION}...", flush=True)
vertexai.init(project=PROJECT_ID, location=LOCATION)

for model_id in CANDIDATES:
    try:
        model = GenerativeModel(model_id)
        response = model.generate_content("Hi", generation_config={"max_output_tokens": 5})
        print(f"CHECK [OK] {model_id}", flush=True)
    except Exception as e:
        print(f"CHECK [FAIL] {model_id}: {str(e)[:50]}", flush=True)

print("Probe complete.", flush=True)
