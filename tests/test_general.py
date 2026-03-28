import pytest
import vertexai
from backend.agents.general import GeneralAgent
from backend.config import get_settings

@pytest.fixture(scope="module")
def init_vertex():
    settings = get_settings()
    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)

@pytest.mark.asyncio
async def test_general_agent_low_urgency(init_vertex):
    agent = GeneralAgent()
    triage_data = {
        "synthesized_context": "User asking about system status.",
        "key_variables": ["status", "system"]
    }
    raw_input = "Is the Omni-Bridge system currently operational?"
    
    result = await agent.run(triage_data, raw_input)
    
    assert "execution_payload" in result
    assert result["execution_payload"]["action_command"] == "log_information_only"
    assert result["execution_payload"]["target_system"] == "General_Incident_Log"
