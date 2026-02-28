# Unity LLM Scene Generator

A Unity 3D game whose environment is built at runtime from LLM output. You describe a scene in plain text, the backend translates it into structured JSON via an LLM, and Unity spawns the geometry.

## How it works

```
Unity  ──(scene description)──►  API  ──(LLM + prompt engineering)──►  scene JSON
       ◄──────────────────────────────────────────────────────────────
```

1. The player (or developer) provides a plain-text scene description
2. Unity POSTs it to the FastAPI backend
3. The backend calls an LLM with structured output constraints
4. Unity receives a JSON list of objects and spawns them as primitives

> The LLM integration is not yet wired up — the backend currently returns a hardcoded mock scene. The schema and Unity-side rendering are fully functional end-to-end.

## Repo structure

```
backend/   Python FastAPI server — scene generation API
unity/     Unity 3D project — third-person game + scene builder
```

## Running locally

**1. Start the backend**

```bash
cd backend
uv sync                  # first time only
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Requires Python 3.13+ and [uv](https://github.com/astral-sh/uv).

**2. Open the Unity project**

Open `unity/` in Unity Editor (2022.3+ recommended). The project uses URP, Cinemachine, and the new Input System.

**3. Generate a scene**

- Enter Play Mode
- In the Inspector, right-click the `SceneBuilder` component on the `SceneManager` GameObject
- Choose **Generate Scene**

The `GeneratedScene` object in the hierarchy will be populated with Unity primitives matching the API response.

## Tech stack

| Layer | Stack |
|---|---|
| Game engine | Unity (URP, Cinemachine, Input System) |
| Backend | Python 3.13, FastAPI, Pydantic |
| Package manager | uv |
| LLM integration | Anthropic API *(coming soon)* |
