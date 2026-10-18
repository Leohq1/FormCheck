from pathlib import Path

import numpy as np
import pytest
from formcheck_pose.landmarks import BackendLandmark
from formcheck_pose.mediapipe_estimator import (
    BackendPose,
    BackendResult,
    EstimatorBuild,
    MediaPipePoseEstimator,
    ModelAssetError,
    PoseEstimationError,
)
from formcheck_pose.models import CANONICAL_LANDMARKS, LandmarkName


class RecordingBackend:
    def __init__(self, result: BackendResult) -> None:
        self.result = result
        self.timestamps: list[int] = []
        self.closed = False

    def detect(self, image_srgb: np.ndarray, timestamp_ms: int) -> BackendResult:
        del image_srgb
        self.timestamps.append(timestamp_ms)
        if timestamp_ms == 40:
            raise RuntimeError(r"C:\secret\model.task exploded")
        return self.result

    def close(self) -> None:
        self.closed = True


def _pose(visibility: float) -> BackendPose:
    return BackendPose(
        [
            BackendLandmark(0.1, 0.2, 0.0, visibility, visibility)
            for _ in CANONICAL_LANDMARKS
        ]
    )


def test_missing_model_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ModelAssetError) as caught:
        MediaPipePoseEstimator(tmp_path / "missing.task")
    assert "missing.task" not in caught.value.safe_message


def test_adapter_uses_video_mode_two_poses_and_primary_pose(tmp_path: Path) -> None:
    model = tmp_path / "pose.task"
    model.write_bytes(b"model")
    builds: list[EstimatorBuild] = []
    backend = RecordingBackend(BackendResult([_pose(0.2), _pose(0.9)]))

    def factory(build: EstimatorBuild) -> RecordingBackend:
        builds.append(build)
        return backend

    estimator = MediaPipePoseEstimator(model, backend_factory=factory, estimator_version="test")
    blank = np.zeros((8, 8, 3), dtype=np.uint8)
    sequence = estimator.infer(tmp_path / "video.mp4", [0, 33], frames=[blank, blank])

    assert builds[0].running_mode == "VIDEO"
    assert builds[0].num_poses == 2
    assert sequence.estimator_name == "mediapipe-pose-landmarker"
    assert sequence.estimator_version == "test"
    assert sequence.model_version == "pose_landmarker_full"
    assert [frame.timestamp_ms for frame in sequence.frames] == [0, 33]
    assert sequence.frames[0].detected_pose_count == 2
    wrist = sequence.frames[0].landmark(LandmarkName.RIGHT_WRIST)
    assert wrist.visibility == 0.9
    assert backend.closed is True


def test_no_pose_frame_is_explicit(tmp_path: Path) -> None:
    model = tmp_path / "pose.task"
    model.write_bytes(b"model")
    backend = RecordingBackend(BackendResult([]))
    estimator = MediaPipePoseEstimator(model, backend_factory=lambda _build: backend)
    blank = np.zeros((4, 4, 3), dtype=np.uint8)
    sequence = estimator.infer(tmp_path / "video.mp4", [15], frames=[blank])

    frame = sequence.frames[0]
    assert frame.detected_pose_count == 0
    assert frame.timestamp_ms == 15
    assert all(item.available is False and item.missing_reason == "no_pose" for item in frame.landmarks)


def test_timestamps_must_be_strictly_increasing_integers(tmp_path: Path) -> None:
    model = tmp_path / "pose.task"
    model.write_bytes(b"model")
    estimator = MediaPipePoseEstimator(model, backend_factory=lambda _build: RecordingBackend(BackendResult([])))

    with pytest.raises(PoseEstimationError):
        estimator.infer(tmp_path / "video.mp4", [10, 10], frames=[])


def test_backend_failure_is_typed_and_omits_paths(tmp_path: Path) -> None:
    model = tmp_path / "pose.task"
    model.write_bytes(b"model")
    backend = RecordingBackend(BackendResult([]))
    estimator = MediaPipePoseEstimator(model, backend_factory=lambda _build: backend)
    blank = np.zeros((4, 4, 3), dtype=np.uint8)

    with pytest.raises(PoseEstimationError) as caught:
        estimator.infer(tmp_path / "video.mp4", [0, 40], frames=[blank, blank])

    assert "secret" not in caught.value.safe_message
    assert backend.closed is True
