import contextvars
from typing import List, Optional, Any
from backend.skills.base import BaseSkill
from backend.skills.security import SecurityGovernanceSkill
from backend.skills.memory import MemoryManagementSkill

# Context variable for holding active skills in the current thread/async task
active_skills_context = contextvars.ContextVar("active_skills", default=[])

class SkillRegistry:
    """Manages the dynamic lookup and instantiation of skills."""
    
    _available_skills = {
        "security": SecurityGovernanceSkill,
        "memory": MemoryManagementSkill
    }

    @classmethod
    def load_skills(cls, skill_names: List[str]):
        """Initializes and sets the active skills for the current context."""
        loaded = []
        for name in skill_names:
            name = name.strip().lower()
            if name in cls._available_skills:
                loaded.append(cls._available_skills[name]())
        active_skills_context.set(loaded)

    @classmethod
    def get_active_skills(cls) -> List[BaseSkill]:
        """Returns the list of skills loaded into the current session state."""
        return active_skills_context.get()

async def execute_pre_processing(text: str, context: Optional[dict] = None) -> tuple[str, dict]:
    """Applies all active skills' pre-processing steps."""
    skills = SkillRegistry.get_active_skills()
    modified_text = text
    modified_ctx = context or {}
    for skill in skills:
        modified_text, modified_ctx = await skill.pre_process(modified_text, modified_ctx)
    return modified_text, modified_ctx

async def execute_post_processing(payload: Any) -> Any:
    """Applies all active skills' post-processing steps."""
    skills = SkillRegistry.get_active_skills()
    modified_payload = payload
    for skill in skills:
        modified_payload = await skill.post_process(modified_payload)
    return modified_payload
