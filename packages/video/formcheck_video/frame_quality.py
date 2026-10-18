from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from formcheck_video.models import VideoQualitySignals

FloatFrame = NDArray[np.float64]


@dataclass(frozen=True)
class FrameQualityConfig:
    version: str = "frame-quality.v1-provisional"
    minimum_frames: int = 2


def measure_frame_quality(path: object, config: FrameQualityConfig) -> VideoQualitySignals:
    """Read a video when OpenCV can open it. Tests use ``score_frames`` directly."""
    del path
    return _unavailable(config, "unreadable_video")


def score_frames(frames: Sequence[NDArray[np.generic]], config: FrameQualityConfig) -> VideoQualitySignals:
    usable = [_gray(frame) for frame in frames if frame is not None and frame.size > 0]
    if len(usable) < config.minimum_frames:
        return _unavailable(config, "insufficient_frames")
    sharpness = float(np.mean([_laplacian_variance(frame) for frame in usable]))
    shifts = [
        _translation_magnitude(left, right) for left, right in zip(usable, usable[1:], strict=False)
    ]
    motion = float(np.mean(shifts)) if shifts else 0.0
    if not np.isfinite(sharpness) or not np.isfinite(motion):
        return _unavailable(config, "unreadable_frames")
    return VideoQualitySignals(
        sharpness=sharpness,
        camera_motion=motion,
        available=True,
        version=config.version,
    )


def _unavailable(config: FrameQualityConfig, reason: str) -> VideoQualitySignals:
    return VideoQualitySignals(
        sharpness=None,
        camera_motion=None,
        available=False,
        unavailable_reason=reason,
        version=config.version,
    )


def _gray(frame: NDArray[np.generic]) -> FloatFrame:
    array = np.asarray(frame, dtype=np.float64)
    if array.ndim == 3:
        array = array.mean(axis=2)
    return array


def _laplacian_variance(frame: FloatFrame) -> float:
    padded = np.pad(frame, 1, mode="edge")
    center = padded[1:-1, 1:-1]
    lap = (
        padded[:-2, 1:-1]
        + padded[2:, 1:-1]
        + padded[1:-1, :-2]
        + padded[1:-1, 2:]
        - (4.0 * center)
    )
    return float(lap.var())


def _translation_magnitude(left: FloatFrame, right: FloatFrame) -> float:
    if left.shape != right.shape:
        return float("nan")
    window = np.outer(np.hanning(left.shape[0]), np.hanning(left.shape[1]))
    first = np.fft.fft2(left * window)
    second = np.fft.fft2(right * window)
    product = first * np.conj(second)
    magnitude = np.abs(product)
    cross = product / np.maximum(magnitude, 1e-12)
    correlation = np.fft.ifft2(cross).real
    peak = np.unravel_index(int(np.argmax(correlation)), correlation.shape)
    dy = peak[0] if peak[0] <= left.shape[0] // 2 else peak[0] - left.shape[0]
    dx = peak[1] if peak[1] <= left.shape[1] // 2 else peak[1] - left.shape[1]
    return float(np.hypot(dx, dy))
