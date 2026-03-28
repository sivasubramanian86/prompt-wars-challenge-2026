"""
Mock stubs for downstream target systems.
Replace with real API clients post-hackathon.
"""
import logging

logger = logging.getLogger(__name__)


class MockEmergencyDispatchAPI:
    """Stub for Emergency_Dispatch_API."""

    @staticmethod
    def dispatch_traffic_response(params: dict) -> dict:
        logger.info(f"[MOCK] Emergency_Dispatch_API.dispatch_traffic_response: {params}")
        return {"status": "dispatched", "unit_id": "UNIT-042", "eta_minutes": 7}

    @staticmethod
    def dispatch_crisis_response(params: dict) -> dict:
        logger.info(f"[MOCK] Emergency_Dispatch_API.dispatch_crisis_response: {params}")
        return {"status": "dispatched", "unit_id": "CRISIS-007", "eta_minutes": 12}


class MockHospitalEHRSystem:
    """Stub for Hospital_EHR_System."""

    @staticmethod
    def dispatch_medical_response(params: dict) -> dict:
        logger.info(f"[MOCK] Hospital_EHR_System.dispatch_medical_response: {params}")
        return {"status": "received", "triage_bed": "ER-3", "on_call_physician": "Dr. Priya"}


class MockCivilDefenseAPI:
    """Stub for Civil_Defense_API."""

    @staticmethod
    def issue_weather_alert(params: dict) -> dict:
        logger.info(f"[MOCK] Civil_Defense_API.issue_weather_alert: {params}")
        return {"status": "alert_issued", "broadcast_channels": ["SMS", "Radio", "App"]}


# Registry — maps target_system → action_command → callable
MOCK_REGISTRY: dict[str, dict] = {
    "Emergency_Dispatch_API": {
        "dispatch_traffic_response": MockEmergencyDispatchAPI.dispatch_traffic_response,
        "dispatch_crisis_response": MockEmergencyDispatchAPI.dispatch_crisis_response,
    },
    "Hospital_EHR_System": {
        "dispatch_medical_response": MockHospitalEHRSystem.dispatch_medical_response,
    },
    "Civil_Defense_API": {
        "issue_weather_alert": MockCivilDefenseAPI.issue_weather_alert,
    },
}


def call_mock_api(target_system: str, action_command: str, parameters: dict) -> dict:
    """Dispatch to the appropriate mock stub."""
    system = MOCK_REGISTRY.get(target_system)
    if not system:
        return {"status": "no_mock_available", "target_system": target_system}
    fn = system.get(action_command)
    if not fn:
        return {"status": "no_action_mock", "action_command": action_command}
    return fn(parameters)
