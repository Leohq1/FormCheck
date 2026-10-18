from formcheck_biomechanics.models import Handedness
from formcheck_biomechanics.normalization import (
    NormalizedFrame,
    NormalizedLandmark,
    NormalizedPoseSequence,
)
from formcheck_biomechanics.signals import MotionSignals
from formcheck_pose.models import CANONICAL_LANDMARKS, LandmarkName


def normalized_wrist_sequence(samples: list[tuple[int, tuple[float, float] | None]]) -> NormalizedPoseSequence:
    frames: list[NormalizedFrame] = []
    for index, (timestamp, point) in enumerate(samples):
        landmarks = []
        for name in CANONICAL_LANDMARKS:
            if name is LandmarkName.RIGHT_WRIST and point is not None:
                landmarks.append(
                    NormalizedLandmark(
                        name=name,
                        available=True,
                        x=point[0],
                        y=point[1],
                        visibility=1.0,
                        presence=1.0,
                    )
                )
            else:
                landmarks.append(NormalizedLandmark(name=name, available=False, missing_reason="not_needed"))
        frames.append(
            NormalizedFrame(
                index=index,
                timestamp_ms=timestamp,
                landmarks=tuple(landmarks),
                scale=1.0,
                scale_source="torso_length",
            )
        )
    return NormalizedPoseSequence(handedness=Handedness.RIGHT, frames=tuple(frames), version="test")


def energy_series(values: list[float | None], *, step_ms: int = 100) -> MotionSignals:
    return MotionSignals(
        timestamps_ms=tuple(index * step_ms for index in range(len(values))),
        wrist_speed=tuple(values),
        energy=tuple(values),
        version="test",
    )
