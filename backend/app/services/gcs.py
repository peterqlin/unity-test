"""
Google Cloud Storage helpers for scene snapshots.

Each iteration of the agent pipeline is saved as:
    gs://<GCS_BUCKET>/scenes/<session_id>/<iteration:02d>_<phase>.json

Phases: "initial", "turn_01" … "turn_NN", "final"
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from google.cloud import storage

from app.core.config import settings
from app.models.scene import SceneResponse

logger = logging.getLogger(__name__)

_client: storage.Client | None = None


def _get_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
    return _client


def new_session_id() -> str:
    return str(uuid.uuid4())


def save_scene_iteration(
    session_id: str,
    iteration: int,
    description: str,
    scene: SceneResponse,
    *,
    phase: str,
) -> str:
    """
    Persist *scene* to GCS and return the blob name.
    Logs a warning and returns "" on failure so the caller is never blocked.
    """
    try:
        client = _get_client()
        bucket = client.bucket(settings.GCS_BUCKET)
        blob_name = f"scenes/{session_id}/{iteration:02d}_{phase}.json"
        blob = bucket.blob(blob_name)

        payload = {
            "session_id": session_id,
            "iteration": iteration,
            "phase": phase,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "object_count": len(scene.objects),
            "light_count": len(scene.lights),
            "scene": json.loads(scene.model_dump_json()),
        }

        blob.upload_from_string(
            json.dumps(payload, indent=2),
            content_type="application/json",
        )
        logger.info(f"GCS saved → gs://{settings.GCS_BUCKET}/{blob_name}")
        return blob_name

    except Exception as exc:
        logger.warning(f"GCS save failed (non-fatal): {exc}")
        return ""
