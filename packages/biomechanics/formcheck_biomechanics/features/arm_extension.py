"""Dominant elbow angle at the highest reliable wrist position."""

from __future__ import annotations

from dataclasses import dataclass

from formcheck_pose.models import LandmarkName

from formcheck_biomechanics.config import SUPPORTED_VIEWS, FeatureConfig
from formcheck_biomechanics.features.base import FeatureContext, FeatureSpec
from formcheck_biomechanics.geometry import elbow_angle_deg, joint_angle_deg
from formcheck_biomechanics.models import FeatureValue as MeasuredFeature
from formcheck_biomechanics.models import ViewHint

FEATURE_NAME = "dominant_elbow_angle_at_max_wrist_height_deg"
FEATURE_VERSION = "1"
MIN_CONFIDENCE = 0.5
NEIGHBORHOOD = 1


@dataclass(frozen=True)
class JointSample:
    timestamp_ms: int
    wrist_height: float
    shoulder: tuple[float, float]
    elbow: tuple[float, float]
    wrist: tuple[float, float]
    confidence: float


@dataclass(frozen=True)
class FeatureValue:
    name: str
    version: str
    unit: str
    value: float | None
    confidence: float | None
    available: bool
    reason: str | None = None


def dominant_elbow_angle_at_max_wrist_height(samples: list[JointSample]) -> FeatureValue:
    reliable = [sample for sample in samples if sample.confidence >= MIN_CONFIDENCE]
    if not reliable:
        return _unavailable("missing_required_landmark")

    peak = max(reliable, key=lambda sample: sample.wrist_height)
    peak_index = samples.index(peak)
    window = samples[max(0, peak_index - NEIGHBORHOOD) : peak_index + NEIGHBORHOOD + 1]
    if any(sample.confidence < MIN_CONFIDENCE for sample in window):
        return _unavailable("unstable_or_unreliable_maximum")

    try:
        angle = elbow_angle_deg(peak.shoulder, peak.elbow, peak.wrist)
    except ValueError:
        return _unavailable("unstable_or_unreliable_maximum")

    confidence = min(sample.confidence for sample in window)
    return FeatureValue(
        name=FEATURE_NAME,
        version=FEATURE_VERSION,
        unit="deg",
        value=angle,
        confidence=confidence,
        available=True,
    )


def _unavailable(reason: str) -> FeatureValue:
    return FeatureValue(
        name=FEATURE_NAME,
        version=FEATURE_VERSION,
        unit="deg",
        value=None,
        confidence=None,
        available=False,
        reason=reason,
    )


class ArmExtensionFeature:
    """Stroke-window extractor. Sample scoring stays in ``dominant_elbow_angle_at_max_wrist_height``."""

    spec = FeatureSpec(
        name=FEATURE_NAME,
        version="1",
        unit="deg",
        required_landmarks=("right_shoulder", "right_elbow", "right_wrist"),
        supported_views=(ViewHint.SIDE, ViewHint.REAR_THREE_QUARTER),
        handedness_policy="canonical_dominant_right",
        confidence_strategy="minimum_required_visibility",
    )

    def __init__(self, config: FeatureConfig | None = None) -> None:
        self.config = config or FeatureConfig()

    def compute(self, context: FeatureContext) -> MeasuredFeature:
        if context.view not in SUPPORTED_VIEWS or context.window is None:
            reason = "unsupported_view" if context.view not in SUPPORTED_VIEWS else "stroke_unavailable"
            return self._missing(reason)
        window_frames = [
            frame
            for frame in context.sequence.frames
            if context.window.start_ms <= frame.timestamp_ms <= context.window.end_ms
        ]
        if any(frame.scale is None for frame in window_frames):
            return self._missing("missing_scale")
        ranked = [frame for frame in window_frames if _wrist_height(frame) is not None]
        if not ranked:
            return self._missing("missing_landmark")
        apparent = max(ranked, key=lambda frame: _wrist_height(frame) or -1)
        if not _reliable(apparent, self.config.minimum_visibility):
            return self._missing("unstable_or_unreliable_maximum")
        neighbors = [
            frame
            for frame in window_frames
            if abs(frame.timestamp_ms - apparent.timestamp_ms) <= self.config.neighborhood_ms
        ]
        if any(
            not _reliable(frame, self.config.minimum_visibility)
            for frame in neighbors
            if _wrist_height(frame) is not None
        ):
            return self._missing("unstable_or_unreliable_maximum")
        angle = joint_angle_deg(
            _xy(apparent, LandmarkName.RIGHT_SHOULDER),
            _xy(apparent, LandmarkName.RIGHT_ELBOW),
            _xy(apparent, LandmarkName.RIGHT_WRIST),
        )
        if angle is None:
            return self._missing("missing_landmark")
        return MeasuredFeature(
            name=FEATURE_NAME,
            value=angle,
            unit="deg",
            confidence=_landmark_confidence(apparent),
            available=True,
            feature_version=self.spec.version,
        )

    def _missing(self, reason: str) -> MeasuredFeature:
        return MeasuredFeature(
            name=FEATURE_NAME,
            available=False,
            feature_version=self.spec.version,
            unavailable_reason=reason,
        )


def _wrist_height(frame: object) -> float | None:
    landmark = frame.landmark(LandmarkName.RIGHT_WRIST)  # type: ignore[attr-defined]
    if landmark.y is None or not landmark.available:
        return None
    return float(landmark.y)


def _xy(frame: object, name: LandmarkName) -> tuple[float, float] | None:
    landmark = frame.landmark(name)  # type: ignore[attr-defined]
    if not landmark.available or landmark.x is None or landmark.y is None:
        return None
    return (float(landmark.x), float(landmark.y))


def _reliable(frame: object, minimum_visibility: float) -> bool:
    names = (LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_ELBOW, LandmarkName.RIGHT_WRIST)
    for name in names:
        landmark = frame.landmark(name)  # type: ignore[attr-defined]
        if not landmark.available or landmark.visibility is None or landmark.visibility < minimum_visibility:
            return False
        if landmark.x is None or landmark.y is None:
            return False
    return True


def _landmark_confidence(frame: object) -> float:
    values = [
        float(frame.landmark(name).visibility)  # type: ignore[attr-defined]
        for name in (LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_ELBOW, LandmarkName.RIGHT_WRIST)
    ]
    return min(values)
