from __future__ import annotations

import math
from dataclasses import dataclass

from formcheck_pose.models import LandmarkName

from formcheck_biomechanics.config import SignalConfig
from formcheck_biomechanics.normalization import NormalizedPoseSequence


@dataclass(frozen=True)
class MotionSignals:
    timestamps_ms: tuple[int, ...]
    wrist_speed: tuple[float | None, ...]
    energy: tuple[float | None, ...]
    version: str


def compute_motion_signals(
    sequence: NormalizedPoseSequence,
    config: SignalConfig | None = None,
) -> MotionSignals:
    settings = config or SignalConfig()
    timestamps = tuple(frame.timestamp_ms for frame in sequence.frames)
    if timestamps != tuple(sorted(set(timestamps))):
        raise ValueError("motion signals require strictly increasing timestamps")
    positions = [_wrist(frame) for frame in sequence.frames]
    speeds: list[float | None] = [None]
    for index in range(1, len(positions)):
        previous = positions[index - 1]
        current = positions[index]
        elapsed = (timestamps[index] - timestamps[index - 1]) / 1000
        if previous is None or current is None or elapsed <= 0:
            speeds.append(None)
            continue
        speeds.append(math.dist(previous, current) / elapsed)
    smoothed = _smooth(timestamps, speeds, settings)
    return MotionSignals(
        timestamps_ms=timestamps,
        wrist_speed=tuple(smoothed),
        energy=tuple(smoothed),
        version=settings.version,
    )


def _wrist(frame: object) -> tuple[float, float] | None:
    landmark = frame.landmark(LandmarkName.RIGHT_WRIST)  # type: ignore[attr-defined]
    if not landmark.available or landmark.x is None or landmark.y is None:
        return None
    return (float(landmark.x), float(landmark.y))


def _smooth(
    timestamps: tuple[int, ...],
    speeds: list[float | None],
    config: SignalConfig,
) -> list[float | None]:
    smoothed: list[float | None] = []
    for index, value in enumerate(speeds):
        if value is None:
            smoothed.append(None)
            continue
        window: list[float] = []
        for other in range(len(speeds)):
            sample = speeds[other]
            if sample is None:
                continue
            if abs(timestamps[other] - timestamps[index]) > config.smoothing_ms:
                continue
            if _crosses_gap(timestamps, speeds, index, other, config.maximum_gap_ms):
                continue
            window.append(sample)
        smoothed.append(sum(window) / len(window) if window else None)
    return smoothed


def _crosses_gap(
    timestamps: tuple[int, ...],
    speeds: list[float | None],
    left: int,
    right: int,
    maximum_gap_ms: int,
) -> bool:
    start, end = sorted((left, right))
    for index in range(start, end):
        if speeds[index] is None or speeds[index + 1] is None:
            if timestamps[index + 1] - timestamps[index] > maximum_gap_ms:
                return True
        elif timestamps[index + 1] - timestamps[index] > maximum_gap_ms:
            return True
    return False
