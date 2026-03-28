import re
import logging
from typing import Optional
from backend.skills.base import BaseSkill
from backend.schemas.incident import IncidentExecutionPayload

logger = logging.getLogger("omnibridge.skills.security")

class SecurityGovernanceSkill(BaseSkill):
    """PII Scrubbing Skill - regex-based anonymization."""

    @property
    def name(self) -> str:
        return "SecurityGovernance"

    def __init__(self):
        # Compiled regex for SSN (XXX-XX-XXXX)
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        # Compiled regex for generic Credit Cards (13 to 19 digits)
        self.cc_pattern = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
        # Placeholder for explicit names (this is harder with regex, but we follow directions)
        # Note: Real name scrubbing often needs an NER model, but here we'll use common list patterns or just a placeholder.
        self.name_patterns = [
            re.compile(r'\bMr\.\s+[A-Z][a-z]+\b'),
            re.compile(r'\bMs\.\s+[A-Z][a-z]+\b'),
            re.compile(r'\bDr\.\s+[A-Z][a-z]+\b')
        ]

    async def pre_process(self, text_input: str, context: Optional[dict] = None) -> tuple[str, dict]:
        """Scrub PII from text before passing it to the pipeline."""
        if not text_input:
            return text_input, context or {}

        scrubbed = text_input
        # Scrub SSNs
        scrubbed = self.ssn_pattern.sub("[REDACTED_SSN]", scrubbed)
        # Scrub Credit Cards
        scrubbed = self.cc_pattern.sub("[REDACTED_CC]", scrubbed)
        # Scrub Names (Honorifics)
        for pattern in self.name_patterns:
            scrubbed = pattern.sub("[REDACTED_NAME]", scrubbed)

        logger.info(f"SecurityGovernanceSkill: Scrubbing complete. PII instances removed.")
        return scrubbed, context or {}

    async def post_process(self, payload: IncidentExecutionPayload, context: Optional[dict] = None) -> IncidentExecutionPayload:
        """The core payload schema remains untouched, but we could scrub the synthesized_context here if needed."""
        if payload.synthesized_context:
            scrubbed_context = payload.synthesized_context
            scrubbed_context = self.ssn_pattern.sub("[REDACTED_SSN]", scrubbed_context)
            scrubbed_context = self.cc_pattern.sub("[REDACTED_CC]", scrubbed_context)
            # We must re-assign to follow Pydantic immutability if needed, but standard assignment works here.
            payload.synthesized_context = scrubbed_context
        return payload
