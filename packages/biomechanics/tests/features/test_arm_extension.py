from formcheck_biomechanics.features.arm_extension import ArmExtensionFeature
from formcheck_biomechanics.features.base import FeatureContext
from formcheck_biomechanics.models import Handedness, StrokeWindow, ViewHint
from formcheck_biomechanics.normalization import (
    NormalizedFrame,
    NormalizedLandmark,
    NormalizedPoseSequence,
)
from formcheck_pose.models import CANONICAL_LANDMARKS, LandmarkName


def _frame(
    timestamp: int,
    shoulder: tuple[float, float],
    elbow: tuple[float, float],
    wrist: tuple[float, float],
    *,
    visibility: float = 1.0,
    scale: float | None = 1.0,
) -> NormalizedFrame:
    points = {
        LandmarkName.RIGHT_SHOULDER: shoulder,
        LandmarkName.RIGHT_ELBOW: elbow,
        LandmarkName.RIGHT_WRIST: wrist,
    }
    landmarks = []
    for name in CANONICAL_LANDMARKS:
        point = points.get(name)
        if point is None:
            landmarks.append(NormalizedLandmark(name=name, available=False, missing_reason="not_needed"))
        else:
            landmarks.append(
                NormalizedLandmark(
                    name=name,
                    available=True,
                    x=point[0],
                    y=point[1],
                    visibility=visibility,
                    presence=visibility,
                )
            )
    return NormalizedFrame(
        index=timestamp,
        timestamp_ms=timestamp,
        landmarks=tuple(landmarks),
        scale=scale,
        scale_source=None if scale is None else "torso_length",
    )


def _context(frames: list[NormalizedFrame], view: ViewHint | None = ViewHint.SIDE) -> FeatureContext:
    return FeatureContext(
        sequence=NormalizedPoseSequence(handedness=Handedness.RIGHT, frames=tuple(frames), version="test"),
        window=StrokeWindow(start_ms=0, end_ms=200, confidence=0.8),
        view=view,
    )


def test_known_geometry_at_maximum_wrist_height_returns_degrees() -> None:
    low = _frame(0, (0.0, 0.0), (0.0, -1.0), (1.0, -1.0))
    high = _frame(40, (0.0, 1.0), (0.0, 0.0), (1.0, 0.0))
    feature = ArmExtensionFeature().compute(_context([low, high]))

    assert feature.available is True
    assert feature.unit == "deg"
    assert feature.feature_version == "1"
    assert feature.value == 90


def test_unreliable_apparent_maximum_is_not_replaced_by_a_neighbor() -> None:
    reliable = _frame(0, (0.0, 1.0), (0.0, 0.0), (1.0, 0.0), visibility=0.9)
    higher_but_unreliable = _frame(40, (0.0, 2.0), (0.0, 1.0), (1.0, 1.0), visibility=0.1)
    feature = ArmExtensionFeature().compute(_context([reliable, higher_but_unreliable]))

    assert feature.available is False
    assert feature.value is None
    assert feature.unavailable_reason == "unstable_or_unreliable_maximum"


def test_unsupported_view_missing_scale_or_landmark_have_no_value() -> None:
    frame = _frame(0, (0.0, 1.0), (0.0, 0.0), (1.0, 0.0))
    unsupported = ArmExtensionFeature().compute(_context([frame], view=None))
    missing_scale = ArmExtensionFeature().compute(_context([_frame(0, (0.0, 1.0), (0.0, 0.0), (1.0, 0.0), scale=None)]))
    missing_wrist = _frame(0, (0.0, 1.0), (0.0, 0.0), (1.0, 0.0))
    cleared = missing_wrist.model_copy(
        update={
            "landmarks": tuple(
                item if item.name is not LandmarkName.RIGHT_WRIST else NormalizedLandmark(name=item.name, available=False, missing_reason="not_detected")
                for item in missing_wrist.landmarks
            )
        }
    )
    missing = ArmExtensionFeature().compute(_context([cleared]))

    assert unsupported.available is False and unsupported.value is None
    assert missing_scale.unavailable_reason == "missing_scale" and missing_scale.value is None
    assert missing.unavailable_reason == "missing_landmark" and missing.value is None
