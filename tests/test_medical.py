import pytest
import vertexai
from backend.agents.medical import MedicalAgent
from backend.config import get_settings

@pytest.fixture(scope="module")
def init_vertex():
    settings = get_settings()
    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)

@pytest.mark.asyncio
async def test_medical_specialist_extraction(init_vertex):
    agent = MedicalAgent()
    triage_data = {
        "synthesized_context": "Patient 45yo male, chest pain.",
        "key_variables": ["45yo male", "chest pain"]
    }
    raw_input = "Patient John Doe, 45, chest pain. Aspirin administered."
    
    result = await agent.run(triage_data, raw_input)
    
    assert "extracted_entities" in result
    assert "execution_payload" in result
    assert result["execution_payload"]["action_command"] == "dispatch_medical_response"
