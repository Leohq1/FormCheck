import numpy as np
from formcheck_video.frame_quality import FrameQualityConfig, score_frames


def _checkerboard(size: int = 64, block: int = 4) -> np.ndarray:
    grid = np.indices((size, size)).sum(axis=0)
    return ((grid // block) % 2 * 255).astype(np.uint8)


def _blur(frame: np.ndarray) -> np.ndarray:
    padded = np.pad(frame.astype(np.float64), 2, mode="edge")
    total = np.zeros(frame.shape, dtype=np.float64)
    for y in range(5):
        for x in range(5):
            total += padded[y : y + frame.shape[0], x : x + frame.shape[1]]
    return total / 25.0


def test_checkerboard_is_sharper_than_its_blur() -> None:
    sharp = _checkerboard()
    blurred = _blur(sharp)
    config = FrameQualityConfig()

    sharp_score = score_frames([sharp, sharp], config)
    blur_score = score_frames([blurred, blurred], config)

    assert sharp_score.available and blur_score.available
    assert sharp_score.sharpness is not None and blur_score.sharpness is not None
    assert sharp_score.sharpness > blur_score.sharpness


def test_full_frame_translation_raises_camera_motion_and_static_does_not() -> None:
    frame = np.zeros((64, 64), dtype=np.float64)
    frame[16:32, 8:24] = 255
    shifted = np.zeros_like(frame)
    shifted[16:32, 16:32] = 255
    config = FrameQualityConfig()

    static = score_frames([frame, frame], config)
    moving = score_frames([frame, shifted], config)

    assert static.camera_motion is not None and moving.camera_motion is not None
    assert static.camera_motion < 1.0
    assert moving.camera_motion > static.camera_motion + 4


def test_insufficient_frames_are_unavailable_rather_than_zero() -> None:
    signals = score_frames([], FrameQualityConfig())

    assert signals.available is False
    assert signals.sharpness is None
    assert signals.camera_motion is None
    assert signals.unavailable_reason == "insufficient_frames"
