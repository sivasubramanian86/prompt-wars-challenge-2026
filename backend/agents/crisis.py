from vertexai.generative_models import GenerativeModel
from backend.config import get_settings
import json

class CrisisAgent:
    """Agentic Step 2: Weather/Fire/Hazmat Crisis Specialist."""
    
    def __init__(self, model_id=None):
        settings = get_settings()
        self.model = GenerativeModel(model_id or settings.synthesis_model)

    async def run(self, triage_data, raw_input):
        prompt = f"""You are the Omni-Bridge Humanitarian Crisis and Search & Rescue Agent.
You process flood, fire, earthquake, and extreme weather reports.
Strict rules:
- extracted_entities: extract people trapped, safe zones, resource needs, severity
- missing_critical_data: e.g., "safe_zone_radius_unknown", "flood_depth_not_confirmed"
- target_system: Civil_Defense_Command
- action_command: allocate_emergency_assets

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
    "missing_critical_data": ["safe_zone_radius_unknown"]
  }},
  "execution_payload": {{
    "target_system": "Civil_Defense_Command",
    "action_command": "allocate_emergency_assets",
    "parameters": {{}}
  }}
}}"""
        response = self.model.generate_content(prompt)
        return self._parse_json(response.text)

    def _parse_json(self, response_text):
        clean = response_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
