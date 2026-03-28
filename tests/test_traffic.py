import pytest
import vertexai
from backend.agents.traffic import TrafficAgent
from backend.config import get_settings

@pytest.fixture(scope="module")
def init_vertex():
    settings = get_settings()
    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)

@pytest.mark.asyncio
async def test_traffic_specialist_routing(init_vertex):
    agent = TrafficAgent()
    triage_data = {
        "synthesized_context": "Multi-car pileup, Route 66 at Miles.",
        "key_variables": ["Route 66", "Miles"]
    }
    raw_input = "Major crash, 3 vehicles, Route 66 junction."
    
    result = await agent.run(triage_data, raw_input)
    
    assert "execution_payload" in result
    assert result["execution_payload"]["target_system"] == "Municipal_Traffic_Control"
