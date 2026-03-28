from vertexai.generative_models import GenerativeModel
from backend.config import get_settings
import json

class TrafficAgent:
    """Agentic Step 2: Traffic/Civic Emergency Specialist."""
    
    def __init__(self, model_id=None):
        settings = get_settings()
        self.model = GenerativeModel(model_id or settings.synthesis_model)

    async def run(self, triage_data, raw_input):
        prompt = f"""You are the Omni-Bridge Civic Emergency Logistics Agent.
You process traffic incidents, gridlock reports, and infrastructure failures.
Strict rules:
- extracted_entities: extract locations, coordinates, vehicle counts, hazard types
- missing_critical_data: e.g., "hazmat_not_confirmed", "precise_gps_missing"
- target_system: Municipal_Traffic_Control
- action_command: update_traffic_signal_route

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
    "missing_critical_data": ["hazmat_not_confirmed"]
  }},
  "execution_payload": {{
    "target_system": "Municipal_Traffic_Control",
    "action_command": "update_traffic_signal_route",
    "parameters": {{}}
  }}
}}"""
        response = self.model.generate_content(prompt)
        return self._parse_json(response.text)

    def _parse_json(self, response_text):
        clean = response_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
