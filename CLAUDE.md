# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This repo contains two separate components:

- `backend/` — Python FastAPI server (see `backend/CLAUDE.md` for backend-specific guidance)
- `unity/` — Unity 3D game project

## Backend

The backend uses Python 3.13+ with `uv`. Always run commands from the `backend/` directory using `uv` — never `pip` or `python` directly.

```bash
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload   # Dev server
uv add <package>                                                      # Add dependency
uv sync                                                               # Install from uv.lock
```

> **Note:** `fastapi dev` crashes on Windows due to an emoji encoding issue in fastapi-cli. Use `uvicorn` directly as shown above.

Settings are loaded via `app/core/config.py` (pydantic-settings). Create a `backend/.env` with `DATABASE_URL` and `SECRET_KEY` before running.

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/scene/generate` | Accept a scene description, return structured scene JSON |

**`POST /scene/generate`** request body:
```json
{ "description": "a grassy arena with pillars" }
```

Response schema (`SceneResponse`): a list of `objects`, each with:

| Field | Type | Notes |
|---|---|---|
| `name` | string | Unique label for the object |
| `type` | enum | `cube` \| `sphere` \| `cylinder` \| `plane` \| `capsule` |
| `position` | `{x, y, z}` | World-space position |
| `rotation` | `{x, y, z}` | Euler angles in degrees |
| `scale` | `{x, y, z}` | Local scale |
| `color` | `{r, g, b}` | Normalized 0–1 float values |
| `has_collider` | bool | Whether to add a collider |
| `is_trigger` | bool | If true, collider is a trigger zone |
| `tag` | string | Unity tag (e.g. `"Ground"`, `"Obstacle"`, `"Collectible"`) |

Pydantic models live in `backend/app/models/scene.py`. The router is at `backend/app/routers/scene.py`. Currently returns a hardcoded mock scene; will be replaced with a real LLM call.

## Unity

The Unity project is in `unity/`. Open it with the Unity Editor — there are no CLI build commands configured. The project uses:

- **Unity Input System** (new) — inputs handled via `StarterAssetsInputs.cs`
- **Cinemachine** — third-person camera via `CinemachineCamera`
- **TextMeshPro** — UI text for collectible counter

### Custom Scripts

All custom game scripts live in `unity/Assets/_Scripts/` and `unity/Assets/SourceFiles/Scripts/`:

| Script | Purpose |
|---|---|
| `ThirdPersonController.cs` | Player movement, jumping, sprinting, camera rotation (StarterAssets namespace) |
| `StarterAssetsInputs.cs` | Input bridge between Unity Input System and the controller |
| `RespawnPlayer.cs` | Respawns player at start position when Y position drops below a threshold; resets camera via `ThirdPersonController.ResetCameraRotation()` |
| `Pickup.cs` | Rotating/bobbing collectible that destroys itself and spawns a particle effect on player collision |
| `UpdateCollectibleCount.cs` | UI script that counts remaining `Pickup` objects and updates a TextMeshProUGUI display |
| `MotionAudioController.cs` | Plays/fades audio based on whether the player is moving |
| `LocalAPICall.cs` | Makes a GET request to `http://127.0.0.1:8000/` on `Start()` and logs the response |

### Unity–Backend Integration

`LocalAPICall.cs` (attached to a scene GameObject) calls the local FastAPI server using `UnityWebRequest` as a coroutine. The backend must be running before entering Play Mode:

```bash
cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
