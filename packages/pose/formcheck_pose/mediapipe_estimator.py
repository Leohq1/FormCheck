from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from formcheck_pose.landmarks import BackendLandmark, map_landmarks
from formcheck_pose.models import PoseFrame, PoseSequence

ESTIMATOR_NAME = "mediapipe-pose-landmarker"
MODEL_VERSION = "pose_landmarker_full"


class PoseEstimationError(Exception):
    def __init__(self, safe_message: str) -> None:
        super().__init__(safe_message)
        self.safe_message = safe_message


class ModelAssetError(PoseEstimationError):
    pass


@dataclass(frozen=True)
class BackendPose:
    landmarks: list[BackendLandmark]


@dataclass(frozen=True)
class BackendResult:
    poses: list[BackendPose]


@dataclass(frozen=True)
class EstimatorBuild:
    running_mode: str
    num_poses: int
    model_path: str


class PoseBackend(Protocol):
    def detect(self, image_srgb: NDArray[np.uint8], timestamp_ms: int) -> BackendResult: ...

    def close(self) -> None: ...


BackendFactory = Callable[[EstimatorBuild], PoseBackend]


class MediaPipePoseEstimator:
    def __init__(
        self,
        model_path: Path,
        *,
        backend_factory: BackendFactory | None = None,
        estimator_version: str = "1.1.1",
    ) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise ModelAssetError("The pose model file was not found.")
        self.estimator_version = estimator_version
        self._factory = backend_factory or _mediapipe_backend

    def infer(
        self,
        video_path: Path,
        timestamps_ms: Sequence[int],
        *,
        frames: Sequence[NDArray[np.uint8]] | None = None,
    ) -> PoseSequence:
        stamps = _validated_timestamps(timestamps_ms)
        images = list(frames) if frames is not None else _read_frames(video_path, stamps)
        if len(images) != len(stamps):
            raise PoseEstimationError("Pose estimation did not receive one frame per timestamp.")
        backend = self._factory(
            EstimatorBuild(running_mode="VIDEO", num_poses=2, model_path=str(self.model_path))
        )
        try:
            pose_frames = tuple(
                _frame(index, timestamp, image, backend) for index, (timestamp, image) in enumerate(zip(stamps, images, strict=True))
            )
        except PoseEstimationError:
            raise
        except Exception as exc:
            raise PoseEstimationError("Pose estimation failed.") from exc
        finally:
            backend.close()
        return PoseSequence(
            estimator_name=ESTIMATOR_NAME,
            estimator_version=self.estimator_version,
            model_version=MODEL_VERSION,
            frames=pose_frames,
        )


def _validated_timestamps(timestamps_ms: Sequence[int]) -> tuple[int, ...]:
    stamps = tuple(timestamps_ms)
    previous: int | None = None
    for timestamp in stamps:
        if isinstance(timestamp, bool) or not isinstance(timestamp, int):
            raise PoseEstimationError("Pose timestamps must be integer milliseconds.")
        if timestamp < 0 or (previous is not None and timestamp <= previous):
            raise PoseEstimationError("Pose timestamps must be strictly increasing.")
        previous = timestamp
    return stamps


def _frame(index: int, timestamp: int, image: NDArray[np.uint8] | None, backend: PoseBackend) -> PoseFrame:
    if image is None:
        return PoseFrame(
            index=index,
            timestamp_ms=timestamp,
            detected_pose_count=0,
            landmarks=map_landmarks(None, missing_reason="frame_unreadable"),
        )
    result = backend.detect(image, timestamp)
    count = len(result.poses)
    primary = _primary_pose(result.poses)
    reason = "no_pose" if primary is None else "not_detected"
    raw = primary.landmarks if primary is not None else None
    return PoseFrame(
        index=index,
        timestamp_ms=timestamp,
        detected_pose_count=count,
        landmarks=map_landmarks(raw, missing_reason=reason),
    )


def _primary_pose(poses: list[BackendPose]) -> BackendPose | None:
    if not poses:
        return None

    def rank(item: tuple[int, BackendPose]) -> tuple[float, int]:
        index, pose = item
        visibilities = [landmark.visibility or 0.0 for landmark in pose.landmarks]
        mean = sum(visibilities) / len(visibilities) if visibilities else 0.0
        return (mean, -index)

    return max(enumerate(poses), key=rank)[1]


def frame_indexes_for_timestamps(timestamps_ms: Sequence[int], fps: float) -> tuple[int, ...]:
    """Map output timestamps onto sequentially decoded frame indexes."""
    if fps <= 0:
        raise PoseEstimationError("The normalized video could not be read.")
    indexes: list[int] = []
    previous = -1
    for timestamp in timestamps_ms:
        index = int(round(float(timestamp) * fps / 1000.0))
        if index < 0:
            index = 0
        if index <= previous:
            index = previous + 1
        indexes.append(index)
        previous = index
    return tuple(indexes)


def _read_frames(video_path: Path, timestamps_ms: Sequence[int]) -> list[NDArray[np.uint8] | None]:
    import cv2

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise PoseEstimationError("The normalized video could not be read.")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    try:
        indexes = frame_indexes_for_timestamps(timestamps_ms, fps)
    except PoseEstimationError:
        capture.release()
        raise
    needed = set(indexes)
    decoded: dict[int, NDArray[np.uint8] | None] = {}
    frame_index = 0
    last_needed = max(indexes) if indexes else -1
    try:
        while frame_index <= last_needed:
            ok, frame = capture.read()
            if frame_index in needed:
                if not ok or frame is None:
                    decoded[frame_index] = None
                else:
                    decoded[frame_index] = np.asarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), dtype=np.uint8)
            if not ok:
                break
            frame_index += 1
    finally:
        capture.release()
    return [decoded.get(index) for index in indexes]


def _mediapipe_backend(build: EstimatorBuild) -> PoseBackend:
    if build.running_mode != "VIDEO" or build.num_poses != 2:
        raise PoseEstimationError("Pose estimator configuration is invalid.")
    return _MediaPipeBackend(Path(build.model_path))


class _MediaPipeBackend:
    def __init__(self, model_path: Path) -> None:
        from mediapipe.tasks.python.core.base_options import BaseOptions  # type: ignore[import-untyped]
        from mediapipe.tasks.python.vision import (  # type: ignore[import-untyped]
            PoseLandmarker,
            PoseLandmarkerOptions,
        )
        from mediapipe.tasks.python.vision.core.vision_task_running_mode import (  # type: ignore[import-untyped]
            VisionTaskRunningMode,
        )

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=VisionTaskRunningMode.VIDEO,
            num_poses=2,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)

    def detect(self, image_srgb: NDArray[np.uint8], timestamp_ms: int) -> BackendResult:
        import mediapipe as mp  # type: ignore[import-untyped]

        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image_srgb))
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        poses: list[BackendPose] = []
        for pose in result.pose_landmarks or []:
            landmarks = [
                BackendLandmark(
                    x=float(landmark.x),
                    y=float(landmark.y),
                    z=float(landmark.z),
                    visibility=float(landmark.visibility) if landmark.visibility is not None else None,
                    presence=float(landmark.presence) if landmark.presence is not None else None,
                )
                for landmark in pose
            ]
            poses.append(BackendPose(landmarks))
        return BackendResult(poses)

    def close(self) -> None:
        self._landmarker.close()
