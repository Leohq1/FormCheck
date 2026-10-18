from __future__ import annotations

from pathlib import Path
from typing import Protocol

from formcheck_pose.models import PoseSequence


class PoseEstimator(Protocol):
    def infer(self, video_path: Path, timestamps_ms: list[int]) -> PoseSequence: ...
