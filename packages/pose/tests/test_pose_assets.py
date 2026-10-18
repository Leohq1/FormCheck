import os
from pathlib import Path

import numpy as np
import pytest
from formcheck_pose.assets import resolve_pose_model_path
from formcheck_pose.mediapipe_estimator import MediaPipePoseEstimator


@pytest.mark.assets
@pytest.mark.integration
def test_pose_model_inference_returns_one_frame_per_timestamp(tmp_path: Path) -> None:
    model = resolve_pose_model_path()
    if model is None:
        pytest.skip("MEDIAPIPE_POSE_MODEL_PATH is not set or does not point to a file")

    import cv2

    video = tmp_path / "blank.mp4"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 30.0, (64, 64))
    if not writer.isOpened():
        pytest.skip("OpenCV could not write a synthetic video")
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    for _ in range(6):
        writer.write(frame)
    writer.release()

    sequence = MediaPipePoseEstimator(model).infer(video, [0, 33, 66])
    assert len(sequence.frames) == 3
    assert [item.timestamp_ms for item in sequence.frames] == [0, 33, 66]
    assert os.environ.get("MEDIAPIPE_POSE_MODEL_PATH")
