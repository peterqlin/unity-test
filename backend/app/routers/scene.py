import json
import logging

from fastapi import APIRouter, HTTPException
from app.models.scene import SceneRequest, SceneResponse
from app.services import gcs, scene_agent, scene_log
from app.services.scene_log import LOG_DIR

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scene", tags=["scene"])

# Fallback scene loaded from a previously-generated log.
_FALLBACK_FILE = LOG_DIR / "2026-03-01_00-04-59_build_a_simple_house.json"
MOCK_SCENE = SceneResponse.model_validate(
    json.loads(_FALLBACK_FILE.read_text(encoding="utf-8"))["scene"]
)


@router.post("/generate", response_model=SceneResponse)
async def generate_scene(request: SceneRequest) -> SceneResponse:
    """
    Accepts a plain-text scene description from Unity and returns a refined
    scene JSON produced by the two-phase agent pipeline:
      1. Structured-output initial generation
      2. Tool-calling critique loop (up to 5 turns, 20 tool calls)
    Every intermediate snapshot is persisted to GCS.
    Falls back to MOCK_SCENE if the pipeline fails.
    """
    logger.info(f'Scene generation requested — description="{request.description}"')
    try:
        scene, session_id = await scene_agent.run(request.description)
        logger.info(f'Scene generation complete — session_id="{session_id}"')
        source = "agent"
    except Exception:
        logger.warning("Agent pipeline unavailable — returning fallback scene (simple house)")
        scene = MOCK_SCENE
        session_id = "fallback"
        source = "mock"

    scene_log.save(request.description, scene, source=source)
    return scene


@router.get("/load/{session_id}", response_model=SceneResponse)
def load_scene(session_id: str) -> SceneResponse:
    """
    Load the final scene for a given session from GCS and return it to Unity.
    The session_id is the UUID subfolder under scenes/ in the GCS bucket.
    Returns 404 if no final scene has been saved for that session.
    """
    logger.info(f'Scene load requested — session_id="{session_id}"')
    try:
        scene = gcs.load_final_scene(session_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Failed to load scene from GCS: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load scene from GCS")
    return scene
