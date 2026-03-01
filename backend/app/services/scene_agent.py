"""
Two-phase agentic scene generation pipeline.

Phase 1 — Initial generation
    A single structured-output call produces a complete SceneResponse from the
    user's description. Saved to GCS as iteration 00_initial.

Phase 2 — Critique loop
    A stateful chat session gives the model a set of surgical editing tools
    (add / replace / remove objects and lights). The model critiques its own
    output and calls tools to fix placement, composition, colour, and lighting.
    Each batch of tool-call results is saved to GCS before the next turn.
    The loop ends when the model calls finish_scene() or the turn / call caps
    are reached. The final scene is saved to GCS as 99_final.

Public API
    run(description) -> (SceneResponse, session_id)
"""

import json
import logging
import time
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.scene import LightObject, SceneObject, SceneResponse
from app.services import gcs

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

_MODEL = "gemini-2.5-flash"
MAX_AGENT_TURNS = 5   # max send→receive cycles in the critique loop
MAX_TOOL_CALLS  = 20  # hard cap on total tool invocations across all turns

# ──────────────────────────────────────────────────────────────────────────────
# Vertex AI client (shared, lazy-initialised)
# ──────────────────────────────────────────────────────────────────────────────

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION,
        )
    return _client


# ──────────────────────────────────────────────────────────────────────────────
# System prompts
# ──────────────────────────────────────────────────────────────────────────────

_INITIAL_SYSTEM_PROMPT = """\
You are a Unity 3D scene designer. Given a scene description, output a list of \
3D primitive objects and light sources that make up that scene.

Object rules:
- Primitive types: cube, sphere, cylinder, plane, capsule
- Ground surfaces use type "plane" with scale x=5, y=1, z=5 (or larger)
- Place objects so they rest on the ground: unit-scale objects have y >= 0.5
- Colors are normalized RGB floats (0.0–1.0)
- Valid tags: "Ground", "Obstacle", "Collectible", "Untagged"
- Collectibles have is_trigger=true and has_collider=true
- Give every object a unique, descriptive name
- Aim for 8–20 objects to make an interesting scene

Light rules:
- Include at most 4 lights per scene to match the mood of the description
- light_type: "directional" for sun/moon, "point" for lamps/fire/orbs, \
"spot" for focused beams
- Always include at least one directional light as the main light source
- Directional: intensity 1.0–2.0; use rotation to set the sun angle \
(e.g. x=50, y=-30, z=0)
- Point / spot: intensity 0.5–5.0, range 5–20 units
"""

_CRITIQUE_SYSTEM_PROMPT = """\
You are a Unity 3D scene quality reviewer with tool access to edit scenes.

Your job: review the provided scene JSON, identify issues, and make targeted \
improvements using the available tools. Call finish_scene() when satisfied.

Review criteria:
1. Description accuracy — does the scene match what was asked for?
2. Object placement — nothing floating, nothing buried underground \
   (y >= 0.5 for unit-scale objects resting on the ground)
3. Composition — objects spread naturally across the space, not all at the origin
4. Colour variety — colours should be distinct and appropriate for each element
5. Lighting — at least one directional light; mood should match the description

Make specific, purposeful edits. Do not rebuild the whole scene — fix what is \
wrong. You MUST make at least 2 tool calls before calling finish_scene().
"""

# ──────────────────────────────────────────────────────────────────────────────
# Tool schema
# ──────────────────────────────────────────────────────────────────────────────

_VEC3 = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "x": types.Schema(type=types.Type.NUMBER),
        "y": types.Schema(type=types.Type.NUMBER),
        "z": types.Schema(type=types.Type.NUMBER),
    },
    required=["x", "y", "z"],
)

_COLOR = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "r": types.Schema(type=types.Type.NUMBER, description="0.0–1.0"),
        "g": types.Schema(type=types.Type.NUMBER, description="0.0–1.0"),
        "b": types.Schema(type=types.Type.NUMBER, description="0.0–1.0"),
    },
    required=["r", "g", "b"],
)

_OBJECT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "name":         types.Schema(type=types.Type.STRING, description="Unique object identifier"),
        "type":         types.Schema(type=types.Type.STRING, enum=["cube", "sphere", "cylinder", "plane", "capsule"]),
        "position":     _VEC3,
        "rotation":     _VEC3,
        "scale":        _VEC3,
        "color":        _COLOR,
        "has_collider": types.Schema(type=types.Type.BOOLEAN),
        "is_trigger":   types.Schema(type=types.Type.BOOLEAN),
        "tag":          types.Schema(type=types.Type.STRING, enum=["Ground", "Obstacle", "Collectible", "Untagged"]),
    },
    required=["name", "type", "position", "rotation", "scale", "color"],
)

_LIGHT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "name":       types.Schema(type=types.Type.STRING),
        "light_type": types.Schema(type=types.Type.STRING, enum=["directional", "point", "spot"]),
        "position":   _VEC3,
        "rotation":   _VEC3,
        "color":      _COLOR,
        "intensity":  types.Schema(type=types.Type.NUMBER, description="directional 1–2, point/spot 0.5–5"),
        "range":      types.Schema(type=types.Type.NUMBER, description="point/spot only; ignored for directional"),
        "spot_angle": types.Schema(type=types.Type.NUMBER, description="spot only, 15–60 degrees; ignored otherwise"),
    },
    required=["name", "light_type", "position", "rotation", "color", "intensity", "range", "spot_angle"],
)

_NAME_ONLY = types.Schema(
    type=types.Type.OBJECT,
    properties={"name": types.Schema(type=types.Type.STRING, description="Name of the item to remove")},
    required=["name"],
)

_SCENE_TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="add_object",
            description=(
                "Add a new 3D primitive to the scene. "
                "Fails if an object with that name already exists — use replace_object instead."
            ),
            parameters=_OBJECT_SCHEMA,
        ),
        types.FunctionDeclaration(
            name="replace_object",
            description=(
                "Replace an existing object with a new definition. "
                "Use this to move, recolour, resize, or change an object's type."
            ),
            parameters=_OBJECT_SCHEMA,
        ),
        types.FunctionDeclaration(
            name="remove_object",
            description="Remove a primitive object from the scene by name.",
            parameters=_NAME_ONLY,
        ),
        types.FunctionDeclaration(
            name="add_light",
            description=(
                "Add a new light to the scene. "
                "Fails if a light with that name already exists — use replace_light instead."
            ),
            parameters=_LIGHT_SCHEMA,
        ),
        types.FunctionDeclaration(
            name="replace_light",
            description="Replace an existing light with a new definition.",
            parameters=_LIGHT_SCHEMA,
        ),
        types.FunctionDeclaration(
            name="remove_light",
            description="Remove a light from the scene by name.",
            parameters=_NAME_ONLY,
        ),
        types.FunctionDeclaration(
            name="finish_scene",
            description=(
                "Signal that you are satisfied with the scene. "
                "Call this only after making all desired improvements."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "assessment": types.Schema(
                        type=types.Type.STRING,
                        description="Brief summary of the improvements made and why the scene is ready.",
                    )
                },
                required=["assessment"],
            ),
        ),
    ]
)

# ──────────────────────────────────────────────────────────────────────────────
# SceneState — mutable scene with tool handlers
# ──────────────────────────────────────────────────────────────────────────────

class SceneState:
    """
    Holds the in-flight scene as plain dicts keyed by object / light name.
    Implements each tool as a method and tracks call counts + finish signal.
    """

    def __init__(self, scene: SceneResponse) -> None:
        self.objects: dict[str, dict] = {
            obj.name: json.loads(obj.model_dump_json()) for obj in scene.objects
        }
        self.lights: dict[str, dict] = {
            light.name: json.loads(light.model_dump_json()) for light in scene.lights
        }
        self.tool_calls: int = 0
        self.finished: bool = False

    # ── scene conversion ──────────────────────────────────────────────────────

    def to_response(self) -> SceneResponse:
        return SceneResponse(
            objects=[SceneObject.model_validate(v) for v in self.objects.values()],
            lights=[LightObject.model_validate(v) for v in self.lights.values()],
        )

    def to_prompt_json(self) -> str:
        return json.dumps(
            {"objects": list(self.objects.values()), "lights": list(self.lights.values())},
            indent=2,
        )

    # ── dispatch ──────────────────────────────────────────────────────────────

    def handle(self, name: str, args: dict) -> dict:
        self.tool_calls += 1
        try:
            match name:
                case "add_object":     return self._add_object(args)
                case "replace_object": return self._replace_object(args)
                case "remove_object":  return self._remove_object(args["name"])
                case "add_light":      return self._add_light(args)
                case "replace_light":  return self._replace_light(args)
                case "remove_light":   return self._remove_light(args["name"])
                case "finish_scene":
                    self.finished = True
                    return {"acknowledged": True, "assessment": args.get("assessment", "")}
                case _:
                    return {"error": f"Unknown tool: {name}"}
        except Exception as exc:
            logger.warning(f"Tool '{name}' raised: {exc}")
            return {"error": str(exc)}

    # ── object tools ──────────────────────────────────────────────────────────

    def _add_object(self, args: dict) -> dict:
        name = args["name"]
        if name in self.objects:
            return {"error": f"'{name}' already exists. Use replace_object."}
        validated = SceneObject.model_validate(args)
        self.objects[name] = json.loads(validated.model_dump_json())
        return {"success": True, "total_objects": len(self.objects)}

    def _replace_object(self, args: dict) -> dict:
        name = args["name"]
        if name not in self.objects:
            return {"error": f"'{name}' not found. Use add_object to create it."}
        validated = SceneObject.model_validate(args)
        self.objects[name] = json.loads(validated.model_dump_json())
        return {"success": True}

    def _remove_object(self, name: str) -> dict:
        if name not in self.objects:
            return {"error": f"'{name}' not found."}
        del self.objects[name]
        return {"success": True, "remaining_objects": len(self.objects)}

    # ── light tools ───────────────────────────────────────────────────────────

    def _add_light(self, args: dict) -> dict:
        name = args["name"]
        if name in self.lights:
            return {"error": f"'{name}' already exists. Use replace_light."}
        validated = LightObject.model_validate(args)
        self.lights[name] = json.loads(validated.model_dump_json())
        return {"success": True, "total_lights": len(self.lights)}

    def _replace_light(self, args: dict) -> dict:
        name = args["name"]
        if name not in self.lights:
            return {"error": f"'{name}' not found. Use add_light."}
        validated = LightObject.model_validate(args)
        self.lights[name] = json.loads(validated.model_dump_json())
        return {"success": True}

    def _remove_light(self, name: str) -> dict:
        if name not in self.lights:
            return {"error": f"'{name}' not found."}
        del self.lights[name]
        return {"success": True}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _deep_dict(obj: Any) -> Any:
    """Recursively convert proto MapComposite / ListValue to plain Python types."""
    if hasattr(obj, "items"):
        return {k: _deep_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_deep_dict(v) for v in obj]
    return obj


# ──────────────────────────────────────────────────────────────────────────────
# Phase 1: Structured-output initial generation
# ──────────────────────────────────────────────────────────────────────────────

async def _generate_initial(description: str) -> SceneResponse:
    client = _get_client()
    logger.info(f"Phase 1 — initial generation: '{description[:80]}'")
    t0 = time.perf_counter()

    response = await client.aio.models.generate_content(
        model=_MODEL,
        contents=f"Generate a Unity 3D scene: {description}",
        config=types.GenerateContentConfig(
            system_instruction=_INITIAL_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=SceneResponse,
        ),
    )

    scene = SceneResponse.model_validate_json(response.text)
    logger.info(
        f"Phase 1 complete: {len(scene.objects)} objects, {len(scene.lights)} lights "
        f"in {time.perf_counter() - t0:.2f}s"
    )
    return scene


# ──────────────────────────────────────────────────────────────────────────────
# Phase 2: Agent critique loop
# ──────────────────────────────────────────────────────────────────────────────

async def _run_critique_loop(
    description: str,
    session_id: str,
    initial_scene: SceneResponse,
) -> SceneResponse:
    client = _get_client()
    state = SceneState(initial_scene)

    chat = client.aio.chats.create(
        model=_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=_CRITIQUE_SYSTEM_PROMPT,
            tools=[_SCENE_TOOLS],
        ),
    )

    critique_prompt = (
        f'Original description: "{description}"\n\n'
        f"Current scene:\n{state.to_prompt_json()}\n\n"
        "Review this scene and improve it using the available tools. "
        "Call finish_scene() when you are satisfied with the result."
    )

    logger.info(f"[{session_id}] Phase 2 — critique loop started")
    response = await chat.send_message(critique_prompt)
    turn = 0

    while (
        not state.finished
        and state.tool_calls < MAX_TOOL_CALLS
        and turn < MAX_AGENT_TURNS
    ):
        if not response.function_calls:
            logger.info(f"[{session_id}] Agent returned no tool calls — stopping")
            break

        # Execute every tool call in this response batch
        result_parts: list[types.Part] = []
        for fc in response.function_calls:
            args = _deep_dict(dict(fc.args) if fc.args else {})
            result = state.handle(fc.name, args)
            logger.info(
                f"[{session_id}] turn={turn + 1}  tool={fc.name}  "
                f"keys={list(args.keys())}  result={result}"
            )
            result_parts.append(
                types.Part.from_function_response(name=fc.name, response=result)
            )

        # Snapshot this turn's state to GCS
        gcs.save_scene_iteration(
            session_id, turn + 1, description, state.to_response(),
            phase=f"turn_{turn + 1:02d}",
        )

        # Always acknowledge tool results, then break if done
        response = await chat.send_message(result_parts)
        turn += 1

        if state.finished:
            break

    logger.info(
        f"[{session_id}] Critique loop done: "
        f"{state.tool_calls} tool calls, {turn} turns, "
        f"finished_signal={state.finished}"
    )
    return state.to_response()


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

async def run(description: str) -> tuple[SceneResponse, str]:
    """
    Execute the full two-phase pipeline and return (final_scene, session_id).
    Every intermediate state is persisted to GCS automatically.
    """
    session_id = gcs.new_session_id()
    logger.info(f"[{session_id}] Agent pipeline started — '{description[:60]}'")
    t0 = time.perf_counter()

    # Phase 1: structured initial generation
    initial_scene = await _generate_initial(description)
    gcs.save_scene_iteration(session_id, 0, description, initial_scene, phase="initial")

    # Phase 2: critique + tool-calling loop
    final_scene = await _run_critique_loop(description, session_id, initial_scene)
    gcs.save_scene_iteration(session_id, 99, description, final_scene, phase="final")

    logger.info(
        f"[{session_id}] Pipeline complete in {time.perf_counter() - t0:.2f}s — "
        f"{len(final_scene.objects)} objects, {len(final_scene.lights)} lights"
    )
    return final_scene, session_id
