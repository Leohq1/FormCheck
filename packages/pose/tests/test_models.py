import pytest
from formcheck_pose.models import (
    CANONICAL_LANDMARKS,
    LandmarkName,
    PoseFrame,
    PoseLandmark,
    PoseSequence,
)
from pydantic import ValidationError


def _unavailable(name: LandmarkName) -> PoseLandmark:
    return PoseLandmark(name=name, available=False, missing_reason="not_detected")


def _frame(index: int, timestamp_ms: int, *, detected_pose_count: int = 1) -> PoseFrame:
    return PoseFrame(
        index=index,
        timestamp_ms=timestamp_ms,
        detected_pose_count=detected_pose_count,
        landmarks=tuple(_unavailable(name) for name in CANONICAL_LANDMARKS),
    )


def test_pose_frame_records_non_negative_index_timestamp_and_pose_count() -> None:
    frame = _frame(0, 0, detected_pose_count=2)

    assert frame.index == 0
    assert frame.timestamp_ms == 0
    assert frame.detected_pose_count == 2
    assert len(frame.landmarks) == len(CANONICAL_LANDMARKS)


def test_unavailable_landmark_has_reason_and_no_coordinates() -> None:
    landmark = _unavailable(LandmarkName.RIGHT_WRIST)

    assert landmark.available is False
    assert landmark.missing_reason == "not_detected"
    assert landmark.x is None
    assert landmark.y is None
    assert landmark.relative_z is None


def test_negative_frame_index_and_timestamp_are_rejected() -> None:
    with pytest.raises(ValidationError):
        _frame(-1, 0)
    with pytest.raises(ValidationError):
        _frame(0, -1)


def test_pose_sequence_rejects_non_monotonic_timestamps() -> None:
    with pytest.raises(ValidationError, match="strictly increasing"):
        PoseSequence(
            estimator_name="fake",
            estimator_version="0",
            model_version="0",
            frames=(_frame(0, 10), _frame(1, 10)),
        )


def test_relative_z_is_labeled_non_metric() -> None:
    landmark = PoseLandmark(
        name=LandmarkName.NOSE,
        available=True,
        x=0.5,
        y=0.4,
        relative_z=-0.2,
        visibility=0.9,
        presence=0.9,
    )

    assert landmark.relative_z == -0.2
    assert "relative_z" in PoseLandmark.model_fields
    assert "z" not in PoseLandmark.model_fields
