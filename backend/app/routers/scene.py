import json
import logging

from fastapi import APIRouter
from app.models.scene import SceneRequest, SceneResponse
from app.services import scene_agent
from app.services import scene_log
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
