from vertexai.generative_models import GenerativeModel
from backend.config import get_settings
import json

class MedicalAgent:
    """Agentic Step 2: Medical Domain Specialist."""
    
    def __init__(self, model_id=None):
        settings = get_settings()
        self.model = GenerativeModel(model_id or settings.synthesis_model)

    async def run(self, triage_data, raw_input):
        prompt = f"""You are the Omni-Bridge Medical Triage Agent.
You process medical crisis data and convert it into a structured, clinician-ready format.
Strict rules:
- extracted_entities: extract patients, ages, medications, dosages, vitals, allergies
- missing_critical_data: list only missing CRITICAL items (e.g., "medication_dosage_not_confirmed")
- target_system: Hospital_EHR_System
- action_command: dispatch_medical_response

Input:
---
Synthesized context: {triage_data['synthesized_context']}
Key variables: {triage_data['key_variables']}
Raw input: {raw_input}
---
Respond ONLY with this JSON:
{{
  "extracted_entities": {{
    "key_variables": ["entity1", "entity2"],
    "missing_critical_data": ["medication_dosage_not_confirmed"]
  }},
  "execution_payload": {{
    "target_system": "Hospital_EHR_System",
    "action_command": "dispatch_medical_response",
    "parameters": {{}}
  }}
}}"""
        response = self.model.generate_content(prompt)
        return self._parse_json(response.text)

    def _parse_json(self, response_text):
        clean = response_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
