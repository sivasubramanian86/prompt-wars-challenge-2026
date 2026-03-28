import google.generativeai as genai
import os

genai.configure(transport='rest') # No API key needed with ADC

MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

print("Probing Generative Language API (AI Studio rest)...", flush=True)

for model_id in MODELS:
    try:
        model = genai.GenerativeModel(model_id)
        response = model.generate_content("Hi")
        print(f"  [OK] {model_id}", flush=True)
    except Exception as e:
        print(f"  [FAIL] {model_id}: {str(e)[:100]}", flush=True)
