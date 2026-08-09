import pytest
import vertexai
from backend.agents.synthesis import SynthesisAgent
from backend.schemas.incident import IncidentExecutionPayload, VerificationFlag
from backend.config import get_settings


@pytest.mark.asyncio
async def test_synthesis_payload_construction(init_vertex):
    agent = SynthesisAgent()
    triage_data = {"domain": "Medical", "urgency_level": "CRITICAL", "synthesized_context": "Patient in cardiac distress."}
    domain_payload = {
        "extracted_entities": {"key_variables": ["John Doe"], "missing_critical_data": []},
        "execution_payload": {"target_system": "Emergency_Medical_Services", "action_command": "dispatch_ambulance", "parameters": {}}
    }
    verification_flag = VerificationFlag.VERIFIED
    raw_input = "Original raw context log."
    
    result = await agent.run(triage_data, domain_payload, verification_flag, raw_input)
    
    assert isinstance(result, IncidentExecutionPayload)
    assert result.verification_flag == VerificationFlag.VERIFIED
    assert result.domain_classification == "Medical"
