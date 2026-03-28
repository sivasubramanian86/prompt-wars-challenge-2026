import vertexai
from vertexai.generative_models import GenerativeModel
import os

PROJECT_ID = "prompt-wars-bengaluru-2026"
REGIONS = ["us-central1", "us-east4", "europe-west1", "asia-south1", "asia-southeast1"]

MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-2.0-flash-lite-preview-02-05"]

for region in REGIONS:
    print(f"\nProbing region: {region}", flush=True)
    vertexai.init(project=PROJECT_ID, location=region)
    for model_id in MODELS:
        try:
            model = GenerativeModel(model_id)
            response = model.generate_content("Hi", generation_config={"max_output_tokens": 5})
            print(f"  [OK] {model_id}", flush=True)
        except Exception as e:
            # Print only first line of error
            err = str(e).split('\n')[0][:80]
            print(f"  [FAIL] {model_id}: {err}", flush=True)
