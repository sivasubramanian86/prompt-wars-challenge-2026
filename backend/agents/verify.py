from backend.schemas.incident import VerificationFlag

class VerificationAgent:
    """Agentic Step 3: Deterministic Rule-Based Verification."""
    
    def run(self, triage_data, domain_payload):
        # ── Deterministic Rule-Based Verification Gate (Anti-Hallucination) ──
        # Rule 1: No critical variables? Require HITL.
        if not triage_data.get('key_variables'):
            return VerificationFlag.PENDING_HITL
            
        # Rule 2: Incomplete critical domain data? Require HITL.
        specialist_info = domain_payload.get('extracted_entities', {})
        if specialist_info.get('missing_critical_data'):
            return VerificationFlag.PENDING_HITL
            
        # Rule 3: Low urgency & clear domain? Auto-Verify.
        if triage_data.get('urgency_level') in ["MODERATE", "LOW"]:
            return VerificationFlag.VERIFIED
            
        # Default: High-stakes requires verification.
        return VerificationFlag.VERIFIED
