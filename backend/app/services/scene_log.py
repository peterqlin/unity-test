"""
Persists every scene generation result to backend/scene_logs/ as a JSON file.

Each file is named:
    YYYY-MM-DD_HH-MM-SS_<description-slug>.json

and contains the full input + output so you can replay or inspect any call.
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from app.models.scene import SceneResponse

logger = logging.getLogger(__name__)

# backend/scene_logs/  (two levels up from this file: services → app → backend)
LOG_DIR = Path(__file__).parent.parent.parent / "scene_logs"


def save(description: str, scene: SceneResponse, *, source: str) -> Path:
    """Write *scene* to a timestamped JSON file. *source* is 'gemini' or 'mock'."""
    LOG_DIR.mkdir(exist_ok=True)

    ts = datetime.now(timezone.utc)
    slug = re.sub(r"[^a-z0-9]+", "_", description.lower())[:40].strip("_")
    filename = f"{ts.strftime('%Y-%m-%d_%H-%M-%S')}_{slug}.json"
    path = LOG_DIR / filename

    payload = {
        "timestamp": ts.isoformat(),
        "source": source,
        "description": description,
        "object_count": len(scene.objects),
        "scene": json.loads(scene.model_dump_json()),
    }

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info(f"Scene log saved → scene_logs/{filename}")
    return path
