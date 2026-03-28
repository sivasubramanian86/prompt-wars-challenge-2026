import time
import logging
import math
from typing import Optional, Dict, List
from backend.skills.base import BaseSkill
from backend.schemas.incident import IncidentExecutionPayload

logger = logging.getLogger("omnibridge.skills.memory")

# In-memory sliding window cache for incidents
# Key: geographic cluster-id or lat_long_bucket
# Value: List of incidents within the last 10 minutes
INCIDENT_CACHE: Dict[str, List[dict]] = {}
TTL_SECONDS = 600  # 10 minute sliding window

class MemoryManagementSkill(BaseSkill):
    """Short and Long-term Memory Skill."""

    @property
    def name(self) -> str:
        return "MemoryManagement"

    def __init__(self, use_redis: bool = False):
        self.use_redis = use_redis
        # Mock Vector Store connection placeholder
        self.vector_store_active = True

    def _get_geo_bucket(self, lat: float, lon: float, precision: int = 1) -> str:
        """Simple grouping by rounding lat/long to a certain decimal precision (radius grouping)."""
        return f"{round(lat, precision)}_{round(lon, precision)}"

    def _clean_cache(self):
        """Purge incidents older than 10 minutes from the cache."""
        now = time.time()
        for bucket in list(INCIDENT_CACHE.keys()):
            # Filters incidents that are still within the TTL
            INCIDENT_CACHE[bucket] = [
                inc for inc in INCIDENT_CACHE[bucket] 
                if now - inc['timestamp'] < TTL_SECONDS
            ]
            if not INCIDENT_CACHE[bucket]:
                del INCIDENT_CACHE[bucket]

    async def pre_process(self, text_input: str, context: Optional[dict] = None) -> tuple[str, dict]:
        """Inject long-term and short-term memory context into the prompt/context."""
        self._clean_cache()
        
        # Mock Long-term Memory Fetch (Vector Store)
        # Search for semantically similar historical incidents.
        long_term_context = "[MOCK_LONG_TERM_MEMORY]: Previous similar flooding incidents in this district (2023)."
        
        enhanced_context = context or {}
        enhanced_context['long_term_memory'] = long_term_context
        
        # Log active context injection
        logger.info(f"MemoryManagementSkill: Injected long-term memory into request context.")
        return text_input, enhanced_context

    async def post_process(self, payload: IncidentExecutionPayload, context: Optional[dict] = None) -> IncidentExecutionPayload:
        """Store the current incident in the sliding window cache."""
        self._clean_cache()
        
        # Try to find geolocation in the synthesized execution parameters
        params = payload.execution_payload.parameters
        lat = params.get('latitude') or params.get('lat')
        lon = params.get('longitude') or params.get('lon') or params.get('lng')

        if lat is not None and lon is not None:
            bucket = self._get_geo_bucket(float(lat), float(lon))
            incident_entry = {
                'id': str(payload.incident_id),
                'timestamp': time.time(),
                'summary': payload.synthesized_context
            }
            if bucket not in INCIDENT_CACHE:
                INCIDENT_CACHE[bucket] = []
            INCIDENT_CACHE[bucket].append(incident_entry)
            
            # Count recent incidents in this radius
            count = len(INCIDENT_CACHE[bucket])
            logger.info(f"MemoryManagementSkill: Recorded incident in bucket {bucket}. Recent count: {count}.")
            
            # Inject short-term summary back into context (if we were to re-process)
            # Or log it for downstream HITL review
            if count > 3:
                payload.urgency_level = "CRITICAL"  # Dynamic Urgency escalation based on frequency
                payload.synthesized_context += f"\n[AUTO-ESCALATION]: {count} related incidents detected within geographic radius in the last 10 mins."

        return payload
