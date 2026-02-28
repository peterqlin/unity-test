# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package Manager

This project uses `uv`. Always use `uv` for running commands and managing dependencies — never use `pip` or `python` directly.

```bash
uv run python app/main.py       # Run the app
uv add <package>                # Add a dependency
uv sync                         # Install/sync dependencies from uv.lock
```

## Running the App

FastAPI is installed but `app/main.py` is currently a placeholder. When a FastAPI app entrypoint is wired up, run the dev server with:

```bash
uv run fastapi dev app/main.py
```

## Configuration

Settings are managed via `app/config.py` using `pydantic-settings`. Required environment variables (loaded from `.env`):

- `DATABASE_URL`
- `SECRET_KEY`

Create a `.env` file at the project root before running the app.

## Architecture

- `app/config.py` — Pydantic `BaseSettings` singleton (`settings`) for typed config from environment/`.env`
- `app/main.py` — Application entry point (currently a stub; FastAPI app will be wired here)

Python 3.13+ is required.
