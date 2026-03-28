import pytest
import vertexai
from backend.agents.crisis import CrisisAgent
from backend.config import get_settings

@pytest.fixture(scope="module")
def init_vertex():
    settings = get_settings()
    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)

@pytest.mark.asyncio
async def test_crisis_agent_hazmat_response(init_vertex):
    agent = CrisisAgent()
    triage_data = {
        "synthesized_context": "Drums leaking yellow gas, chemical warehouse.",
        "key_variables": ["drums", "yellow gas", "warehouse"]
    }
    raw_input = "Chemical leak, hazardous material odor, drums identified."
    
    result = await agent.run(triage_data, raw_input)
    
    assert "execution_payload" in result
    assert result["execution_payload"]["action_command"] == "allocate_emergency_assets"
