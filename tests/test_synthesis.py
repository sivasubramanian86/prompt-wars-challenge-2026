import pytest
import vertexai
from backend.agents.synthesis import SynthesisAgent
from backend.schemas.incident import IncidentExecutionPayload, VerificationFlag
from backend.config import get_settings

@pytest.fixture(scope="module")
def init_vertex():
    settings = get_settings()
    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)

@pytest.mark.asyncio
async def test_synthesis_payload_construction(init_vertex):
    agent = SynthesisAgent()
    triage_data = {"domain": "Medical", "urgency_level": "CRITICAL", "synthesized_context": "..."}
    domain_payload = {"extracted_entities": {}, "execution_payload": {}}
    verification_flag = VerificationFlag.VERIFIED
    raw_input = "Original raw context log."
    
    result = await agent.run(triage_data, domain_payload, verification_flag, raw_input)
    
    assert isinstance(result, IncidentExecutionPayload)
    assert result.verification_flag == VerificationFlag.VERIFIED
    assert result.domain_classification == "Medical"
