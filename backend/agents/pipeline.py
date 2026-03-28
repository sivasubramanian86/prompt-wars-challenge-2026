import logging
from typing import Optional
from google.cloud import pubsub_v1
import json
import vertexai

from backend.config import get_settings
from backend.schemas.incident import VerificationFlag
from backend.agents.transcription import TranscriptionAgent
from backend.agents.triage import TriageAgent
from backend.agents.medical import MedicalAgent
from backend.agents.traffic import TrafficAgent
from backend.agents.crisis import CrisisAgent
from backend.agents.general import GeneralAgent
from backend.agents.verify import VerificationAgent
from backend.agents.synthesis import SynthesisAgent
from backend.tools.gcs_ingest import resolve_gcs_uri

logger = logging.getLogger("omnibridge.pipeline")

class OmniBridgePipeline:
    """The Core Orchestrator for Omni-Bridge.
    It manages the sequential flow of incidents across specialized, autonomous agents.
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize Vertex AI globally for all sub-agents
        vertexai.init(
            project=self.settings.gcp_project_id, 
            location=self.settings.gcp_location
        )
        
        # ── Step 0: Transcription ──
        self.transcriber = TranscriptionAgent()
        
        # ── Step 1: Triage ──
        self.triage_agent = TriageAgent()
        
        # ── Step 2: Specialized Domains ──
        self.specialists = {
            "Medical": MedicalAgent(),
            "Traffic": TrafficAgent(),
            "Weather": CrisisAgent(),
            "Crisis_Response": CrisisAgent(),
            "General": GeneralAgent()
        }
        
        # ── Step 3: Verification ──
        self.verifier = VerificationAgent()
        
        # ── Step 4: Synthesis ──
        self.synthesis_agent = SynthesisAgent()
        
        # ── Step 5: HITL (Pub/Sub) ──
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(
            self.settings.gcp_project_id, 
            self.settings.pubsub_topic_hitl
        )

    async def run(self, 
                  text_input: Optional[str] = None, 
                  audio_bytes: Optional[bytes] = None, 
                  audio_mime: Optional[str] = None,
                  image_part: Optional[any] = None):
        """Executes the full 5-step Agentic Pipeline."""
        
        # Step 0: Audio Handling (if provided)
        raw_context = text_input or ""
        if audio_bytes and audio_mime:
            logger.info("Step 0: Transcribing audio...")
            raw_context = await self.transcriber.run(audio_bytes, audio_mime)
        
        # Step 1: Modality Triage
        logger.info("Step 1: Ingesting & Triaging...")
        triage_data = await self.triage_agent.run(text_input=raw_context, image_part=image_part)
        
        # Step 2: Specialist Routing
        domain = triage_data.get("domain", "General")
        specialist = self.specialists.get(domain, self.specialists["General"])
        logger.info(f"Step 2: Routing to Specialist [{domain}]...")
        specialist_pkg = await specialist.run(triage_data, raw_context)
        
        # Step 3: Verification Gate
        logger.info("Step 3: Verification Check...")
        v_flag = self.verifier.run(triage_data, specialist_pkg)
        
        # Step 4: Synthesis
        logger.info("Step 4: Synthesizing Payload...")
        final_payload = await self.synthesis_agent.run(
            triage_data, 
            specialist_pkg, 
            v_flag, 
            raw_context
        )
        
        # Step 5: HITL Handoff (if needed)
        if final_payload.verification_flag == VerificationFlag.PENDING_HITL:
            logger.info("Step 5: Pushing to HITL Queue (Pub/Sub)...")
            self._publish_to_hitl(final_payload)
            
        return final_payload

    async def run_from_gcs(self, gcs_uri: str):
        """Handy entrypoint for GCS-native ingestion."""
        logger.info(f"Step 0: Resolving GCS URI [{gcs_uri}]...")
        resolved = resolve_gcs_uri(gcs_uri)
        
        return await self.run(
            text_input=resolved.raw_text,
            audio_bytes=resolved.audio_bytes,
            audio_mime=resolved.audio_mime,
            image_part=resolved.image_part
        )

    def _publish_to_hitl(self, payload):
        """Publishes the unverified payload to the Human-in-the-loop Pub/Sub topic."""
        try:
            data = payload.model_dump_json().encode("utf-8")
            self.publisher.publish(self.topic_path, data)
        except Exception as e:
            logger.error(f"Failed to publish to HITL topic: {e}")
            # Do not raise - we want to return the payload even if Pub/Sub fails locally
