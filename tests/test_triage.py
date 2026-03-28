import pytest
import vertexai
from backend.agents.triage import TriageAgent
from backend.config import get_settings

@pytest.fixture(scope="module")
def init_vertex():
    settings = get_settings()
    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)

@pytest.mark.asyncio
async def test_triage_text_medical(init_vertex):
    agent = TriageAgent()
    text = "Severe chest pain, possible heart attack. Patient 65yo male."
    result = await agent.run(text_input=text)
    
    assert result["domain"] == "Medical"
    assert result["urgency_level"] in ["CRITICAL", "HIGH"]
    assert "synthesized_context" in result

@pytest.mark.asyncio
async def test_triage_text_traffic(init_vertex):
    agent = TriageAgent()
    text = "Gridlock on Highway 101 due to a minor fender bender."
    result = await agent.run(text_input=text)
    
    assert result["domain"] == "Traffic"
    assert "urgency_level" in result
