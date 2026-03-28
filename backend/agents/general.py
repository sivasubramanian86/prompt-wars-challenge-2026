from vertexai.generative_models import GenerativeModel
from backend.config import get_settings
import json

class GeneralAgent:
    """Agentic Step 2: General Triage Specialist for unclassified/low-urgency cases."""
    
    def __init__(self, model_id=None):
        settings = get_settings()
        self.model = GenerativeModel(model_id or settings.synthesis_model)

    async def run(self, triage_data, raw_input):
        prompt = f"""You are the Omni-Bridge General Information and Intake Agent.
You process non-emergency queries or incidents that don't fit specific critical protocols.
Strict rules:
- extracted_entities: summarize query and any identifiable nouns
- missing_critical_data: list if the intent is still ambiguous
- target_system: General_Incident_Log
- action_command: log_information_only

Input:
---
Synthesized context: {triage_data['synthesized_context']}
Key variables: {triage_data['key_variables']}
Raw input: {raw_input}
---
Respond ONLY with this JSON:
{{
  "extracted_entities": {{
    "key_variables": ["query_summary"],
    "missing_critical_data": []
  }},
  "execution_payload": {{
    "target_system": "General_Incident_Log",
    "action_command": "log_information_only",
    "parameters": {{}}
  }}
}}"""
        response = self.model.generate_content(prompt)
        return self._parse_json(response.text)

    def _parse_json(self, response_text):
        clean = response_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
