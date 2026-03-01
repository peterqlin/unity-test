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
objects and light sources that make up that scene.

Object rules:
- Primitive types: cube, sphere, cylinder, plane, capsule
- Ground surfaces use type "plane" with scale x=5, y=1, z=5 (or larger)
- Place objects so they rest on the ground: unit-scale objects have y >= 0.5
- Colors are normalized RGB floats (0.0-1.0)
- Valid tags: "Ground", "Obstacle", "Collectible", "Untagged"
- Collectibles have is_trigger=true and has_collider=true
- Give every object a unique, descriptive name
- Aim for 8-20 objects to make an interesting scene

Light rules:
- Include at most 4 lights per scene to match the mood of the description
- light_type: "directional" for sun/moon, "point" for lamps/fire/orbs, "spot" for focused beams
- Directional: position is irrelevant; use rotation to set the sun angle (e.g. x=50, y=-30, z=0)
- Point: intensity 0.5-5.0, range 5-20 units
- Spot: intensity 0.5-5.0, range 5-20 units, spot_angle 15-60 degrees
- Directional: intensity 1.0-2.0
- Light colors: warm white (r=1,g=0.95,b=0.8) for daylight, orange (r=1,g=0.6,b=0.2) for fire/torches,
  cool blue (r=0.6,g=0.8,b=1) for moonlight/magic
- Always include at least one directional light as the main light source
"""

_MODEL = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION,
        )
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
        f"Gemini responded in {elapsed:.2f}s — {len(scene.objects)} objects, {len(scene.lights)} lights"
    )
    return scene
