from abc import ABC, abstractmethod
from typing import Any, Optional
from backend.schemas.incident import IncidentExecutionPayload

class BaseSkill(ABC):
    """Abstract base class for all Omni-Bridge optional skills."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def pre_process(self, text_input: str, context: Optional[dict] = None) -> tuple[str, dict]:
        """Mutate input text or context before pipeline execution."""
        return text_input, context or {}

    @abstractmethod
    async def post_process(self, payload: IncidentExecutionPayload, context: Optional[dict] = None) -> IncidentExecutionPayload:
        """Mutate final payload after pipeline execution."""
        return payload
