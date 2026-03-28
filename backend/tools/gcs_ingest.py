"""
GCS ingestion helper — resolves a gs:// URI to the format
the pipeline expects:
  - text/*         → downloads content, returns as raw_text
  - image/*        → returns Vertex AI Part (inline reference)
  - audio/*        → downloads bytes, returns for transcription
"""

import mimetypes
import logging
from typing import Optional

from google.cloud import storage
from vertexai.generative_models import Part

logger = logging.getLogger(__name__)

# Map file extensions the mimetypes library misses
_EXT_OVERRIDE = {
    ".txt":  "text/plain",
    ".log":  "text/plain",
    ".json": "application/json",
    ".wav":  "audio/wav",
    ".mp3":  "audio/mpeg",
    ".ogg":  "audio/ogg",
    ".webm": "audio/webm",
    ".flac": "audio/flac",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
    ".webp": "image/webp",
}


def detect_mime_type(gcs_uri: str) -> str:
    """Detect MIME type from GCS URI file extension."""
    path = gcs_uri.split("?")[0]
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext in _EXT_OVERRIDE:
        return _EXT_OVERRIDE[ext]
    guessed, _ = mimetypes.guess_type(path)
    return guessed or "application/octet-stream"


def parse_gcs_uri(gcs_uri: str) -> tuple[str, str]:
    """Parse gs://bucket/path into (bucket_name, blob_name)."""
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Not a valid GCS URI: {gcs_uri}")
    without_scheme = gcs_uri[5:]
    bucket, _, blob = without_scheme.partition("/")
    return bucket, blob


class GCSIngestionResult:
    """Typed result from GCS resolution — tells the pipeline what it received."""

    def __init__(
        self,
        raw_text: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        audio_mime: Optional[str] = None,
        image_part: Optional[Part] = None,
        image_mime: Optional[str] = None,
        source_uri: str = "",
        detected_mime: str = "",
    ):
        self.raw_text = raw_text
        self.audio_bytes = audio_bytes
        self.audio_mime = audio_mime
        self.image_part = image_part
        self.image_mime = image_mime
        self.source_uri = source_uri
        self.detected_mime = detected_mime


def resolve_gcs_uri(gcs_uri: str) -> GCSIngestionResult:
    """
    Resolve a GCS URI into a pipeline-ready payload.

    Text  → downloads and decodes bytes.
    Audio → downloads bytes (pipeline transcribes via Gemini).
    Image → creates a Vertex AI Part.from_uri (no download needed).
    """
    mime_type = detect_mime_type(gcs_uri)
    logger.info(f"GCS resolution: uri={gcs_uri} detected_mime={mime_type}")

    if mime_type.startswith("text/") or mime_type == "application/json":
        bucket_name, blob_name = parse_gcs_uri(gcs_uri)
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        content = blob.download_as_text(encoding="utf-8")
        return GCSIngestionResult(raw_text=content, source_uri=gcs_uri, detected_mime=mime_type)

    elif mime_type.startswith("audio/"):
        bucket_name, blob_name = parse_gcs_uri(gcs_uri)
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        audio_bytes = blob.download_as_bytes()
        return GCSIngestionResult(
            audio_bytes=audio_bytes, audio_mime=mime_type,
            source_uri=gcs_uri, detected_mime=mime_type
        )

    elif mime_type.startswith("image/"):
        # Vertex AI can reference GCS images directly — no download needed
        image_part = Part.from_uri(uri=gcs_uri, mime_type=mime_type)
        return GCSIngestionResult(
            image_part=image_part, image_mime=mime_type,
            source_uri=gcs_uri, detected_mime=mime_type
        )

    else:
        raise ValueError(
            f"Unsupported MIME type '{mime_type}' for GCS URI: {gcs_uri}\n"
            "Supported: text/*, audio/*, image/*"
        )
