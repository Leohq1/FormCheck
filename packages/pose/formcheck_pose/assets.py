from __future__ import annotations

import os
from pathlib import Path


def resolve_pose_model_path() -> Path | None:
    raw = os.environ.get("MEDIAPIPE_POSE_MODEL_PATH")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_file() else None
