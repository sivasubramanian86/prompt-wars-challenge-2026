from vertexai.generative_models import GenerativeModel, Part
import os

class TranscriptionAgent:
    """Agentic Step 0: Multi-modal audio transcription."""
    
    def __init__(self, model_id="gemini-2.5-flash"):
        self.model = GenerativeModel(model_id)

    async def run(self, audio_bytes: bytes, mime_type: str) -> str:
        audio_part = Part.from_data(data=audio_bytes, mime_type=mime_type)
        response = self.model.generate_content(
            [
                "You are an expert crisis transcription agent. Transcribe the following audio exactly. If there is background noise, focus on the speaker's intent and medical/logistics data.",
                audio_part
            ]
        )
        return response.text.strip()
