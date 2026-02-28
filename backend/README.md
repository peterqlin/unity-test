# Unity Scene Generator — Backend

FastAPI server that accepts a scene description and returns structured scene JSON for Unity to consume.

## Prerequisites

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)

## Setup

1. **Install dependencies**

   ```bash
   uv sync
   ```

2. **Create a `.env` file** in the `backend/` directory:

   ```env
   DATABASE_URL=sqlite:///./dev.db
   SECRET_KEY=your-secret-key-here
   ```

## Running the server

From the `backend/` directory:

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

> **Note:** Do not use `fastapi dev` on Windows — it crashes due to an emoji encoding issue in fastapi-cli.

The server will be available at `http://127.0.0.1:8000`.

Interactive API docs: `http://127.0.0.1:8000/docs`

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/scene/generate` | Generate scene JSON from a description |

### POST /scene/generate

**Request body:**
```json
{ "description": "a grassy arena with pillars" }
```

**Response** — a list of scene objects, each with:

| Field | Type | Notes |
|---|---|---|
| `name` | string | Unique label |
| `type` | enum | `cube` \| `sphere` \| `cylinder` \| `plane` \| `capsule` |
| `position` | `{x, y, z}` | World-space position |
| `rotation` | `{x, y, z}` | Euler angles in degrees |
| `scale` | `{x, y, z}` | Local scale |
| `color` | `{r, g, b}` | Normalized 0–1 floats |
| `has_collider` | bool | Whether to add a collider |
| `is_trigger` | bool | If true, collider is a trigger zone |
| `tag` | string | Unity tag (e.g. `"Ground"`, `"Obstacle"`, `"Collectible"`) |

Currently returns a hardcoded mock scene. LLM integration is pending.
