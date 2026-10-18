from __future__ import annotations

from dataclasses import dataclass

from formcheck_biomechanics.config import PhaseConfig
from formcheck_biomechanics.models import PhaseEstimate, PhaseName, PhaseSet, StrokeWindow
from formcheck_biomechanics.normalization import NormalizedPoseSequence
from formcheck_biomechanics.signals import MotionSignals


@dataclass(frozen=True)
class PhaseDetectionResult:
    phases: PhaseSet
    contact_dependent_rules_suppressed: bool


def detect_phases(
    sequence: NormalizedPoseSequence,
    window: StrokeWindow,
    signals: MotionSignals,
    config: PhaseConfig | None = None,
) -> PhaseDetectionResult:
    del sequence
    settings = config or PhaseConfig()
    samples = [
        (timestamp, energy)
        for timestamp, energy in zip(signals.timestamps_ms, signals.energy, strict=True)
        if window.start_ms <= timestamp <= window.end_ms and energy is not None
    ]
    if not samples:
        empty = _unavailable_phases("no_motion_in_window")
        return PhaseDetectionResult(PhaseSet(phases=empty, contact_available=False, version=settings.version), True)
    contact_time, contact_energy = max(samples, key=lambda item: item[1])
    start = window.start_ms
    end = window.end_ms
    loading_at = start + max(1, (contact_time - start) // 3)
    acceleration_at = start + max(2, ((contact_time - start) * 2) // 3)
    follow_ms = end - contact_time
    follow_available = follow_ms >= settings.minimum_follow_through_ms
    median = sorted(energy for _, energy in samples)[len(samples) // 2]
    contrast = 0.0 if contact_energy <= 0 else (contact_energy - median) / contact_energy
    contact_uncertainty = max(0.0, min(1.0, 1.0 - contrast))
    contact_available = contact_uncertainty <= settings.contact_uncertainty_limit
    phases = [
        _phase(PhaseName.PREPARATION, start, loading_at, 0.6, 0.4, True, None),
        _phase(PhaseName.LOADING, loading_at, acceleration_at, 0.6, 0.4, True, None),
        _phase(PhaseName.ACCELERATION, acceleration_at, contact_time, 0.7, 0.3, True, None),
        _phase(
            PhaseName.CONTACT,
            contact_time,
            contact_time,
            0.8 if contact_available else 0.4,
            contact_uncertainty,
            contact_available,
            None if contact_available else "uncertain_contact_proxy",
        ),
        _phase(
            PhaseName.FOLLOW_THROUGH,
            contact_time,
            end,
            0.7 if follow_available else 0.2,
            0.3 if follow_available else 0.8,
            follow_available,
            None if follow_available else "insufficient_follow_through",
        ),
    ]
    return PhaseDetectionResult(
        phases=PhaseSet(phases=phases, contact_available=contact_available, version=settings.version),
        contact_dependent_rules_suppressed=not contact_available,
    )


def _phase(
    name: PhaseName,
    start_ms: int,
    end_ms: int,
    confidence: float,
    uncertainty: float,
    available: bool,
    reason: str | None,
) -> PhaseEstimate:
    return PhaseEstimate(
        name=name,
        start_ms=start_ms,
        end_ms=end_ms,
        confidence=confidence,
        uncertainty=uncertainty,
        available=available,
        unavailable_reason=reason,
        evidence=["body_motion_proxy"] if name is PhaseName.CONTACT else ["wrist_speed"],
    )


def _unavailable_phases(reason: str) -> list[PhaseEstimate]:
    return [
        PhaseEstimate(
            name=name,
            confidence=0.0,
            uncertainty=1.0,
            available=False,
            unavailable_reason=reason,
        )
        for name in PhaseName
    ]
