"""
Omni-Bridge Core Pipeline — 5-step sequential agent orchestration via Vertex AI.

Steps:
  0. Audio transcription (Gemini multimodal — if audio provided)
  1. Modality Triage + Intent/Urgency extraction
  2. Domain Specialist routing (Medical / Traffic / Weather / Crisis / General)
  3. Verification & Grounding — rule-based gate (deterministic, not LLM-decided)
  4. Action Synthesis → deterministic IncidentExecutionPayload

Hallucination guard: verification_flag is assigned by rule engine, never by LLM.
"""

import asyncio
import json
import logging
import re
import uuid
from typing import Optional

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part

from backend.tools.gcs_ingest import resolve_gcs_uri

from backend.config import get_settings
from backend.schemas.incident import (
    DomainClassification,
    ExecutionPayload,
    ExtractedEntities,
    IncidentExecutionPayload,
    UrgencyLevel,
    VerificationFlag,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Vertex AI initialised once at module load ──────────────────────────────────
vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)

_JSON_CFG = GenerationConfig(response_mime_type="application/json", temperature=0.1)

# ── Specialist routing tables ──────────────────────────────────────────────────
_SPECIALIST = {
    "Medical": (
        "You are Medical_Triage_Agent. Extract: patient_identifier, symptoms list, "
        "medications with dosages (include mg/ml values), allergies, vital_signs, actions_required. "
        "Flag missing_critical_data for: medication_dosage, patient_identifier, allergies.",
        "Hospital_EHR_System",
        "dispatch_medical_response",
    ),
    "Traffic": (
        "You are Civic_Emergency_Agent (Traffic). Extract: location or GPS coords, "
        "incident_type, vehicles_involved count, injuries_reported, road_blocked boolean, "
        "emergency_services_required list. "
        "Flag missing_critical_data for: exact_location, injury_count.",
        "Emergency_Dispatch_API",
        "dispatch_traffic_response",
    ),
    "Weather": (
        "You are Civic_Emergency_Agent (Weather). Extract: affected_area, weather_type, "
        "severity, population_at_risk, infrastructure_impact, evacuation_needed boolean. "
        "Flag missing_critical_data for: affected_area_bounds, evacuation_status.",
        "Civil_Defense_API",
        "issue_weather_alert",
    ),
    "Crisis_Response": (
        "You are Civic_Emergency_Agent (Crisis). Extract: location, crisis_nature, "
        "casualties, threat_level, resources_required list, containment_status. "
        "Flag missing_critical_data for: exact_location, casualty_count, threat_contained.",
        "Emergency_Dispatch_API",
        "dispatch_crisis_response",
    ),
    "General": (
        "You are General_Triage_Agent. Extract all actionable entities and determine response.",
        "General_Response_API",
        "general_dispatch",
    ),
}

_DOMAIN_MAP = {
    "Medical": DomainClassification.MEDICAL,
    "Traffic": DomainClassification.TRAFFIC,
    "Weather": DomainClassification.WEATHER,
    "Crisis_Response": DomainClassification.CRISIS_RESPONSE,
    "General": DomainClassification.GENERAL,
}
_URGENCY_MAP = {
    "CRITICAL": UrgencyLevel.CRITICAL,
    "HIGH": UrgencyLevel.HIGH,
    "MODERATE": UrgencyLevel.MODERATE,
    "LOW": UrgencyLevel.LOW,
}
_FLAG_MAP = {
    "PASS": VerificationFlag.PASS_,
    "FAIL": VerificationFlag.FAIL,
    "REQUIRES_HUMAN_IN-THE-LOOP": VerificationFlag.HUMAN_IN_LOOP,
}


class OmniBridgePipeline:
    """Stateless pipeline — safe to share across FastAPI requests."""

    def __init__(self) -> None:
        self._triage_model = GenerativeModel(settings.triage_model, generation_config=_JSON_CFG)
        self._synthesis_model = GenerativeModel(settings.synthesis_model, generation_config=_JSON_CFG)
        self._pubsub_client = None

    # ── Public entry point ──────────────────────────────────────────────────────
    async def run(
        self,
        text_input: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        audio_mime: str = "audio/webm",
    ) -> IncidentExecutionPayload:
        # Step 0: Transcribe audio if present
        raw_text = text_input or ""
        if audio_bytes:
            transcript = await asyncio.to_thread(
                self._transcribe_audio, audio_bytes, audio_mime
            )
            raw_text = f"{raw_text}\n\n[Audio Transcript]: {transcript}".strip()

        if not raw_text:
            raise ValueError("At least one of text or audio input is required.")

        # Step 1+2: Triage → domain + urgency + key variables
        triage = await asyncio.to_thread(self._triage_and_urgency, raw_text)
        logger.info(json.dumps({
            "event": "triage_complete",
            "domain": triage.get("domain"),
            "urgency": triage.get("urgency_level"),
        }))

        # Step 3: Domain specialist extraction
        specialist = await asyncio.to_thread(self._route_to_specialist, raw_text, triage)

        # Step 4: Deterministic verification gate
        verification = self._verify_and_ground(triage, specialist)

        # Step 5: Assemble validated payload
        payload = self._synthesize_payload(triage, specialist, verification)

        # HITL: Publish to Cloud Pub/Sub for human review if flagged
        if payload.verification_flag == VerificationFlag.HUMAN_IN_LOOP:
            await asyncio.to_thread(self._publish_hitl, payload)

        return payload

    # ── GCS entry point ───────────────────────────────────────────────────────────────
    async def run_from_gcs(self, gcs_uri: str) -> IncidentExecutionPayload:
        """Resolve a GCS URI and route it through the pipeline.

        Supports:
          - Text files (.txt, .log, .json) — downloaded and treated as raw_text
          - Audio files (.wav, .mp3, .webm, .flac) — downloaded, then transcribed
          - Image files (.jpg, .png, .webp) — passed as Part.from_uri to Gemini
        """
        ingested = await asyncio.to_thread(resolve_gcs_uri, gcs_uri)
        logger.info(json.dumps({
            "event": "gcs_ingested",
            "uri": gcs_uri,
            "mime": ingested.detected_mime,
        }))

        if ingested.raw_text is not None:
            return await self.run(text_input=ingested.raw_text)

        if ingested.audio_bytes is not None:
            return await self.run(
                audio_bytes=ingested.audio_bytes,
                audio_mime=ingested.audio_mime or "audio/wav",
            )

        if ingested.image_part is not None:
            return await self._run_image(ingested.image_part, ingested.image_mime or "image/jpeg")

        raise ValueError("GCS resolution produced no usable payload.")

    async def _run_image(
        self, image_part: Part, mime_type: str
    ) -> IncidentExecutionPayload:
        """Image-specific pipeline: multimodal triage then standard verification/synthesis."""
        triage = await asyncio.to_thread(self._triage_image, image_part)
        logger.info(json.dumps({
            "event": "image_triage_complete",
            "domain": triage.get("domain"),
            "urgency": triage.get("urgency_level"),
        }))
        specialist = await asyncio.to_thread(
            self._route_to_specialist, triage.get("synthesized_context", ""), triage
        )
        verification = self._verify_and_ground(triage, specialist)
        payload = self._synthesize_payload(triage, specialist, verification)
        if payload.verification_flag == VerificationFlag.HUMAN_IN_LOOP:
            await asyncio.to_thread(self._publish_hitl, payload)
        return payload

    # ── Step 0: Audio transcription ────────────────────────────────────────────
    def _transcribe_audio(self, audio_bytes: bytes, mime_type: str) -> str:
        model = GenerativeModel("gemini-2.0-flash-001")
        audio_part = Part.from_data(data=audio_bytes, mime_type=mime_type)
        response = model.generate_content(
            [
                audio_part,
                (
                    "Transcribe this audio verbatim. If multiple speakers are present, "
                    "label them as Speaker 1, Speaker 2, etc. Return only the transcription text."
                ),
            ]
        )
        return response.text.strip()

    def _triage_image(self, image_part: Part) -> dict:
        """Multimodal triage for image inputs — reads scanned forms, photos, sensor dashboards."""
        prompt = """You are the Omni-Bridge Modality Triage and Intent Extraction Agent.

Carefully examine this image. It may be a handwritten form, dashcam photo, control room display,
sensor readout, document scan, or any other visual incident record.

Extract all visible information and classify it. Strict rules:
- domain: exactly one of Medical, Traffic, Weather, Crisis_Response, General
- urgency_level: exactly one of CRITICAL, HIGH, MODERATE, LOW
- synthesized_context: exactly 2 sentences, factual, no speculation
- key_variables: all readable entities (names, numbers, locations, medications, dates, readings)

Respond ONLY with this JSON, no markdown or extra text:
{
  "domain": "Medical",
  "urgency_level": "CRITICAL",
  "synthesized_context": "First sentence. Second sentence.",
  "key_variables": ["entity1", "entity2"]
}"""
        response = self._triage_model.generate_content([image_part, prompt])
        return self._parse_json(response.text)


    def _triage_and_urgency(self, raw_text: str) -> dict:
        prompt = f"""You are the Omni-Bridge Modality Triage and Intent Extraction Agent.

Analyze the input and classify it. Strict rules:
- domain: exactly one of Medical, Traffic, Weather, Crisis_Response, General
- urgency_level: exactly one of CRITICAL, HIGH, MODERATE, LOW
- synthesized_context: exactly 2 sentences, factual, no speculation
- key_variables: all named entities (people, medications, locations, times, coordinates, IDs)

Input:
---
{raw_text}
---

Respond ONLY with this JSON, no markdown or extra text:
{{
  "domain": "Medical",
  "urgency_level": "CRITICAL",
  "synthesized_context": "First sentence. Second sentence.",
  "key_variables": ["entity1", "entity2"]
}}"""
        response = self._triage_model.generate_content(prompt)
        return self._parse_json(response.text)

    # ── Step 3: Domain Specialist ──────────────────────────────────────────────
    def _route_to_specialist(self, raw_text: str, triage: dict) -> dict:
        domain = triage.get("domain", "General")
        instruction, target_system, action_command = _SPECIALIST.get(
            domain, _SPECIALIST["General"]
        )

        prompt = f"""{instruction}

Input:
---
{raw_text}
---

Pre-extracted context:
- Domain: {domain}
- Urgency: {triage.get("urgency_level")}
- Known entities: {triage.get("key_variables", [])}

Respond ONLY with this JSON:
{{
  "extracted_params": {{}},
  "missing_critical_data": [],
  "confidence": 0.85,
  "specialist_notes": "brief analysis"
}}"""
        response = self._triage_model.generate_content(prompt)
        result = self._parse_json(response.text)
        result["target_system"] = target_system
        result["action_command"] = action_command
        return result

    # ── Step 4: Verification & Grounding (DETERMINISTIC — no LLM) ─────────────
    def _verify_and_ground(self, triage: dict, specialist: dict) -> dict:
        domain = triage.get("domain", "General")
        params = specialist.get("extracted_params", {})
        params_str = json.dumps(params).lower()
        violations: list[str] = []

        if domain == "Medical":
            has_dosage = any(
                kw in params_str for kw in ("dosage", "mg", "ml", "mcg", "units")
            )
            if not has_dosage:
                violations.append("medication_dosage_not_confirmed")
            has_patient = any(
                k in params for k in ("patient_id", "patient_name", "patient", "name")
            )
            if not has_patient:
                violations.append("patient_identifier_missing")

        if domain in ("Traffic", "Crisis_Response"):
            has_loc = any(
                kw in params_str
                for kw in ("location", "gps", "coordinates", "address", "street", "lat", "lon")
            )
            if not has_loc:
                violations.append("exact_location_not_confirmed")

        all_missing = list(
            dict.fromkeys(violations + specialist.get("missing_critical_data", []))
        )
        confidence = float(specialist.get("confidence", 0.5))

        if violations or confidence < 0.60 or all_missing:
            flag = "REQUIRES_HUMAN_IN-THE-LOOP"
        else:
            flag = "PASS"

        return {
            "verification_flag": flag,
            "missing_critical_data": all_missing,
            "confidence": confidence,
        }

    # ── Step 5: Payload Assembly ───────────────────────────────────────────────
    def _synthesize_payload(
        self, triage: dict, specialist: dict, verification: dict
    ) -> IncidentExecutionPayload:
        base_vars = triage.get("key_variables", [])
        param_vars = [
            f"{k}: {v}" for k, v in specialist.get("extracted_params", {}).items()
        ]
        all_vars = list(dict.fromkeys(base_vars + param_vars))

        return IncidentExecutionPayload(
            incident_id=uuid.uuid4(),
            domain_classification=_DOMAIN_MAP.get(
                triage.get("domain", "General"), DomainClassification.GENERAL
            ),
            urgency_level=_URGENCY_MAP.get(
                triage.get("urgency_level", "LOW"), UrgencyLevel.LOW
            ),
            synthesized_context=triage.get("synthesized_context", ""),
            extracted_entities=ExtractedEntities(
                key_variables=all_vars,
                missing_critical_data=verification.get("missing_critical_data", []),
            ),
            verification_flag=_FLAG_MAP.get(
                verification.get("verification_flag", "REQUIRES_HUMAN_IN-THE-LOOP"),
                VerificationFlag.HUMAN_IN_LOOP,
            ),
            execution_payload=ExecutionPayload(
                target_system=specialist.get("target_system", "General_Response_API"),
                action_command=specialist.get("action_command", "general_dispatch"),
                parameters=specialist.get("extracted_params", {}),
            ),
        )

    # ── HITL: Cloud Pub/Sub ────────────────────────────────────────────────────
    def _publish_hitl(self, payload: IncidentExecutionPayload) -> None:
        try:
            from google.cloud import pubsub_v1

            if self._pubsub_client is None:
                self._pubsub_client = pubsub_v1.PublisherClient()

            topic_path = self._pubsub_client.topic_path(
                settings.gcp_project_id, settings.pubsub_topic_hitl
            )
            data = json.dumps(payload.model_dump(mode="json"), default=str).encode("utf-8")
            attrs = {
                "incident_id": str(payload.incident_id),
                "urgency_level": payload.urgency_level.value,
                "domain": payload.domain_classification.value,
            }
            future = self._pubsub_client.publish(topic_path, data, **attrs)
            future.result(timeout=10)
            logger.info(
                "hitl_published",
                extra={"incident_id": str(payload.incident_id), "topic": settings.pubsub_topic_hitl},
            )
        except Exception as exc:
            # Non-blocking — HITL failure must not kill the response
            logger.error(json.dumps({"event": "hitl_publish_failed", "error": str(exc)}))

    # ── Utility ────────────────────────────────────────────────────────────────
    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Strip markdown code fences then parse JSON.

        Gemini occasionally wraps output in ```json ... ``` even when
        response_mime_type='application/json' is set. This makes json.loads
        fail silently. We strip fences defensively before every parse.
        """
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(json.dumps({"event": "json_parse_error", "raw_snippet": raw[:200]}))
            raise ValueError(f"LLM returned non-parseable JSON: {exc}") from exc
