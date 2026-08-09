import pytest
import google.auth
import google.auth.exceptions

@pytest.fixture(scope="module")
def init_vertex():
    try:
        google.auth.default()
    except Exception as e:
        pytest.skip(f"GCP Application Default Credentials not available: {e}")
    
    import vertexai
    from backend.config import get_settings
    settings = get_settings()
    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
