from pydantic import BaseModel, Field
from enum import Enum
from uuid import UUID
from typing import Literal


class DomainClassification(str, Enum):
    MEDICAL = "Medical"
    TRAFFIC = "Traffic"
    WEATHER = "Weather"
    CRISIS_RESPONSE = "Crisis_Response"
    GENERAL = "General"


class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class VerificationFlag(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    PENDING_HITL = "PENDING_HITL"


class ExtractedEntities(BaseModel):
    key_variables: list[str]
    missing_critical_data: list[str]  # explicit empty = verified clean


class ExecutionPayload(BaseModel):
    target_system: str
    action_command: str
    parameters: dict


class IncidentExecutionPayload(BaseModel):
    incident_id: UUID
    domain_classification: DomainClassification
    urgency_level: UrgencyLevel
    synthesized_context: str = Field(min_length=10, max_length=600)
    extracted_entities: ExtractedEntities
    verification_flag: VerificationFlag
    execution_payload: ExecutionPayload
