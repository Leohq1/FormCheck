from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from formcheck_pose.models import CANONICAL_LANDMARKS, LandmarkName, PoseLandmark

MEDIAPIPE_INDEX: dict[LandmarkName, int] = {
    name: index for index, name in enumerate(CANONICAL_LANDMARKS)
}


@dataclass(frozen=True)
class BackendLandmark:
    x: float
    y: float
    z: float
    visibility: float | None
    presence: float | None


def map_landmarks(
    raw: Sequence[BackendLandmark | None] | None,
    *,
    missing_reason: str,
) -> tuple[PoseLandmark, ...]:
    landmarks: list[PoseLandmark] = []
    for name in CANONICAL_LANDMARKS:
        item = None if raw is None else raw[MEDIAPIPE_INDEX[name]] if MEDIAPIPE_INDEX[name] < len(raw) else None
        if item is None:
            landmarks.append(PoseLandmark(name=name, available=False, missing_reason=missing_reason))
            continue
        landmarks.append(
            PoseLandmark(
                name=name,
                available=True,
                x=item.x,
                y=item.y,
                relative_z=item.z,
                visibility=item.visibility,
                presence=item.presence,
            )
        )
    return tuple(landmarks)
