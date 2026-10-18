from __future__ import annotations

from dataclasses import dataclass

from formcheck_pose.models import LandmarkName

from formcheck_biomechanics.models import Handedness, ViewHint


@dataclass(frozen=True)
class NormalizationConfig:
    version: str = "normalization.v1-provisional"
    minimum_scale_px: float = 1e-3


@dataclass(frozen=True)
class QualityConfig:
    """Unvalidated engineering defaults. These are not calibrated technique gates."""

    version: str = "quality.v1-provisional"
    minimum_visibility: float = 0.5
    minimum_coverage: float = 0.8
    maximum_occlusion_ms: int = 200
    maximum_camera_motion: float = 6.0
    minimum_sharpness: float = 20.0


@dataclass(frozen=True)
class SignalConfig:
    version: str = "signals.v1-provisional"
    smoothing_ms: int = 60
    maximum_gap_ms: int = 120


@dataclass(frozen=True)
class SegmentationConfig:
    version: str = "segmentation.v1-provisional"
    energy_threshold: float = 0.8
    dominance_ratio: float = 0.75
    context_ms: int = 150
    window_pad_ms: int = 200


@dataclass(frozen=True)
class PhaseConfig:
    version: str = "phases.v1-provisional"
    minimum_follow_through_ms: int = 120
    contact_uncertainty_limit: float = 0.5


@dataclass(frozen=True)
class QualityContext:
    view_hint: ViewHint | None
    sharpness: float | None = None
    camera_motion: float | None = None
    low_resolution: bool = False
    ends_before_follow_through: bool = False


@dataclass(frozen=True)
class FeatureConfig:
    version: str = "1"
    minimum_visibility: float = 0.5
    neighborhood_ms: int = 40


SUPPORTED_VIEWS = frozenset({ViewHint.SIDE, ViewHint.REAR_THREE_QUARTER})
DOMINANT_ARM = {
    Handedness.RIGHT: (LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_ELBOW, LandmarkName.RIGHT_WRIST),
    Handedness.LEFT: (LandmarkName.LEFT_SHOULDER, LandmarkName.LEFT_ELBOW, LandmarkName.LEFT_WRIST),
}
