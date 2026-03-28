from vertexai.generative_models import GenerativeModel
from backend.config import get_settings
from backend.schemas.incident import IncidentExecutionPayload, VerificationFlag
import json
import uuid

class SynthesisAgent:
    """Agentic Step 4: Final JSON Payload Synthesis."""
    
    def __init__(self, model_id=None):
        settings = get_settings()
        self.model = GenerativeModel(model_id or settings.synthesis_model)

    async def run(self, triage_data, domain_payload, verification_flag, raw_input):
        prompt = f"""Synthesize the final CRISIS EXECUTION PAYLOAD.
Combine the triage intent with the specialist domain extraction and the verification flag.
Produce a mission-critical, deterministic JSON object.

Triage: {json.dumps(triage_data)}
Domain Data: {json.dumps(domain_payload)}
Verification Status: {verification_flag.value}
Raw Context: {raw_input}

Respond ONLY with this JSON structure:
{{
  "domain_classification": "Medical | Traffic | Weather | Crisis_Response | General",
  "urgency_level": "CRITICAL | HIGH | MODERATE | LOW",
  "synthesized_context": "Two sentence final summary.",
  "extracted_entities": {{
    "key_variables": [],
    "missing_critical_data": []
  }},
  "execution_payload": {{
    "target_system": "System_Name",
    "action_command": "Command_Name",
    "parameters": {{}}
  }}
}}"""
        response = self.model.generate_content(prompt)
        data = self._parse_json(response.text)
        
        return IncidentExecutionPayload(
            incident_id=uuid.uuid4(),
            domain_classification=data['domain_classification'],
            urgency_level=data['urgency_level'],
            synthesized_context=data['synthesized_context'],
            extracted_entities=data['extracted_entities'],
            verification_flag=verification_flag,
            execution_payload=data['execution_payload']
        )

    def _parse_json(self, response_text):
        clean = response_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
