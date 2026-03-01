import logging
import time

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.scene import SceneResponse

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

SYSTEM_PROMPT = """\
You are a Unity 3D scene designer. Given a scene description, output a list of 3D primitive \
objects that make up that scene.

Rules:
- Primitive types: cube, sphere, cylinder, plane, capsule
- Ground surfaces use type "plane" with scale x=5, y=1, z=5 (or larger)
- Place objects so they rest on the ground: unit-scale objects have y >= 0.5
- Colors are normalized RGB floats (0.0–1.0)
- Valid tags: "Ground", "Obstacle", "Collectible", "Untagged"
- Collectibles have is_trigger=true and has_collider=true
- Give every object a unique, descriptive name
- Aim for 8–20 objects to make an interesting scene
"""

_MODEL = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def generate_scene(description: str) -> SceneResponse:
    client = _get_client()

    preview = description[:80] + ("…" if len(description) > 80 else "")
    logger.info(f'Calling Gemini  model={_MODEL}  description="{preview}"')

    start = time.perf_counter()
    try:
        response = await client.aio.models.generate_content(
            model=_MODEL,
            contents=f"Generate a Unity 3D scene: {description}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=SceneResponse,
            ),
        )
    except Exception as exc:
        elapsed = time.perf_counter() - start
        logger.error(f"Gemini request failed after {elapsed * 1000:.0f}ms — {exc}")
        raise

    elapsed = time.perf_counter() - start

    scene = SceneResponse.model_validate_json(response.text)
    logger.info(
        f"Gemini responded in {elapsed:.2f}s — {len(scene.objects)} objects generated"
    )
    return scene
