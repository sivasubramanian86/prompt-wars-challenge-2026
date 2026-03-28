from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gcp_project_id: str = "prompt-wars-bengaluru-2026"
    gcp_location: str = "us-central1"
    pubsub_topic_hitl: str = "omnibridge-hitl-queue"
    # Vertex AI model IDs — gemini-1.5-flash is GA on all projects.
    # Run list_available_models.py to check if gemini-2.0-flash is accessible.
    # Vertex AI model IDs — verified available for this project via probe.
    triage_model: str = "gemini-2.5-flash-lite"
    synthesis_model: str = "gemini-2.5-flash"
    environment: str = "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
