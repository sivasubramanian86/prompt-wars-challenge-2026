import pytest
from backend.agents.pipeline import OmniBridgePipeline
from backend.schemas.incident import IncidentExecutionPayload, VerificationFlag

@pytest.mark.asyncio
async def test_pipeline_smoke_medical():
    """Smoke test to verify the orchestrated pipeline handles medical text input."""
    pipeline = OmniBridgePipeline()
    raw_text = "Patient John Doe, 45, reported chest pain. Allergic to aspirin. Needs urgent EMS."
    
    result = await pipeline.run(text_input=raw_text)
    
    assert isinstance(result, IncidentExecutionPayload)
    assert result.domain_classification == "Medical"
    assert result.urgency_level in ["CRITICAL", "HIGH"]
    assert "John Doe" in str(result.extracted_entities)

@pytest.mark.asyncio
async def test_pipeline_smoke_traffic():
    """Smoke test for traffic incident orchestration."""
    pipeline = OmniBridgePipeline()
    raw_text = "Multi-car pileup at the intersection of Main and 5th. No injuries reported, but gridlock is severe."
    
    result = await pipeline.run(text_input=raw_text)
    
    assert isinstance(result, IncidentExecutionPayload)
    assert result.domain_classification == "Traffic"
    assert result.urgency_level in ["MODERATE", "HIGH"]
