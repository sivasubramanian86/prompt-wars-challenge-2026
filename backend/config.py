from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gcp_project_id: str = "prompt-wars-bengaluru-2026"
    gcp_location: str = "us-central1"
    pubsub_topic_hitl: str = "omnibridge-hitl-queue"
    # Vertex AI model IDs
    triage_model: str = "gemini-2.0-flash"
    synthesis_model: str = "gemini-2.0-flash"
    environment: str = "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
