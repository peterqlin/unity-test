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
uv run fastapi dev app/main.py   # Start dev server at http://127.0.0.1:8000
uv add <package>                 # Add a dependency
uv sync                          # Install/sync from uv.lock
```

Settings are loaded via `app/core/config.py` (pydantic-settings). Create a `backend/.env` with `DATABASE_URL` and `SECRET_KEY` before running.

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

`LocalAPICall.cs` (attached to a scene GameObject) calls the local FastAPI server using `UnityWebRequest` as a coroutine. The backend must be running (`uv run fastapi dev app/main.py`) before entering Play Mode for the API call to succeed.
