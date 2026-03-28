import pytest
from backend.agents.verify import VerificationAgent
from backend.schemas.incident import VerificationFlag

def test_verify_agent_failed_logic():
    agent = VerificationAgent()
    
    # Case 1: Missing all key variables (Critical Failure)
    triage_data = {"key_variables": [], "urgency_level": "CRITICAL"}
    domain_payload = {"extracted_entities": {"missing_critical_data": []}}
    
    result = agent.run(triage_data, domain_payload)
    assert result == VerificationFlag.PENDING_HITL

def test_verify_agent_missing_specialist_data():
    agent = VerificationAgent()
    
    # Case 2: Specialist identified a missing critical field (e.g., precise location missing)
    triage_data = {"key_variables": ["John Doe"], "urgency_level": "HIGH"}
    domain_payload = {"extracted_entities": {"missing_critical_data": ["precise_gps_missing"]}}
    
    result = agent.run(triage_data, domain_payload)
    assert result == VerificationFlag.PENDING_HITL

def test_verify_agent_pass_low_urgency():
    agent = VerificationAgent()
    
    # Case 3: Simple, low-urgency case with variables
    triage_data = {"key_variables": ["Road Block"], "urgency_level": "LOW"}
    domain_payload = {"extracted_entities": {"missing_critical_data": []}}
    
    result = agent.run(triage_data, domain_payload)
    assert result == VerificationFlag.VERIFIED
