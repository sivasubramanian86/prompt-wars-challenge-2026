from vertexai.generative_models import GenerativeModel, Part
from backend.config import get_settings
import json

class TriageAgent:
    """Agentic Step 1: Modality Triage & Intent Extraction."""
    
    def __init__(self, model_id=None):
        settings = get_settings()
        self.model = GenerativeModel(model_id or settings.triage_model)

    async def run(self, text_input=None, image_part=None):
        if image_part:
            return self._triage_image(image_part)
        return self._triage_text(text_input)

    def _triage_text(self, text):
        prompt = f"""You are the Omni-Bridge Modality Triage and Intent Extraction Agent.
Analyze the input and classify it. Strict rules:
- domain: exactly one of Medical, Traffic, Weather, Crisis_Response, General
- urgency_level: exactly one of CRITICAL, HIGH, MODERATE, LOW
- synthesized_context: exactly 2 sentences, factual, no speculation
- key_variables: all named entities (people, medications, locations, times, coordinates, IDs)

Input:
---
{text}
---
Respond ONLY with this JSON, no markdown:
{{
  "domain": "Medical",
  "urgency_level": "CRITICAL",
  "synthesized_context": "First sentence. Second sentence.",
  "key_variables": ["entity1", "entity2"]
}}"""
        response = self.model.generate_content(prompt)
        return self._parse_json(response.text)

    def _triage_image(self, image_part):
        prompt = """You are the Omni-Bridge Modality Triage and Intent Extraction Agent.
Carefully examine this image (scanned form, photo, dashboard).
Extract all visible information and classify it. Strict rules:
- domain: exactly one of Medical, Traffic, Weather, Crisis_Response, General
- urgency_level: exactly one of CRITICAL, HIGH, MODERATE, LOW
- synthesized_context: exactly 2 sentences, factual, no speculation
- key_variables: all readable entities (names, numbers, locations, medications, dates, readings)

Respond ONLY with this JSON, no markdown:
{
  "domain": "Medical",
  "urgency_level": "CRITICAL",
  "synthesized_context": "First sentence. Second sentence.",
  "key_variables": ["entity1", "entity2"]
}"""
        response = self.model.generate_content([image_part, prompt])
        return self._parse_json(response.text)

    def _parse_json(self, response_text):
        clean = response_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
