import pytest
from backend.tools.gcs_ingest import resolve_gcs_uri, detect_mime_type

def test_detect_mime_type_rules():
    assert detect_mime_type("gs://bucket/incident.txt") == "text/plain"
    assert detect_mime_type("gs://bucket/form.png") == "image/png"
    assert detect_mime_type("gs://bucket/call.wav") == "audio/wav"

def test_resolve_gcs_uri_invalid_scheme():
    with pytest.raises(ValueError, match="Unsupported MIME type"):
        resolve_gcs_uri("https://storage.googleapis.com/...")

@pytest.mark.skip(reason="Requires live GCS access and bucket permissions for prompt-wars-bengaluru-2026")
def test_resolve_gcs_uri_live_text():
    # This would only run on the service account with access to the samples bucket
    uri = "gs://omnibridge-samples-pwb2026/samples/01_medical_er_voice_transcript.txt"
    result = resolve_gcs_uri(uri)
    assert result.raw_text is not None
    assert "Patient" in result.raw_text
