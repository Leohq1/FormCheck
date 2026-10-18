"""Dominant elbow angle at the highest reliable wrist position."""

from __future__ import annotations

from dataclasses import dataclass

from formcheck_biomechanics.geometry import elbow_angle_deg

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
