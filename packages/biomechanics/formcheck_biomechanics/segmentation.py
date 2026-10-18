from __future__ import annotations

from dataclasses import dataclass

from formcheck_biomechanics.config import SegmentationConfig
from formcheck_biomechanics.models import StrokeWindow
from formcheck_biomechanics.signals import MotionSignals


@dataclass(frozen=True)
class MotionCandidate:
    timestamp_ms: int
    energy: float


@dataclass(frozen=True)
class SegmentationResult:
    window: StrokeWindow | None
    competing_candidates: int
    candidates: tuple[MotionCandidate, ...]
    reason: str | None


def segment_overhead_clear(
    signals: MotionSignals,
    config: SegmentationConfig | None = None,
) -> SegmentationResult:
    settings = config or SegmentationConfig()
    peaks = _peaks(signals, settings.energy_threshold)
    if not peaks:
        return SegmentationResult(None, 0, (), "no_candidate")
    if signals.timestamps_ms:
        start = signals.timestamps_ms[0]
        end = signals.timestamps_ms[-1]
    else:
        start = end = 0
    contextual = [
        peak
        for peak in peaks
        if peak.timestamp_ms - start >= settings.context_ms and end - peak.timestamp_ms >= settings.context_ms
    ]
    if not contextual:
        return SegmentationResult(None, len(peaks), tuple(peaks), "insufficient_context")
    ordered = tuple(sorted(contextual, key=lambda item: item.energy, reverse=True))
    if len(ordered) >= 2 and ordered[1].energy >= settings.dominance_ratio * ordered[0].energy:
        return SegmentationResult(None, len(ordered), ordered, "competing_candidates")
    dominant = ordered[0]
    window = StrokeWindow(
        start_ms=max(start, dominant.timestamp_ms - settings.window_pad_ms),
        end_ms=min(end, dominant.timestamp_ms + settings.window_pad_ms),
        confidence=0.7,
    )
    return SegmentationResult(window, 1, ordered, None)


def _peaks(signals: MotionSignals, threshold: float) -> list[MotionCandidate]:
    peaks: list[MotionCandidate] = []
    for index, energy in enumerate(signals.energy):
        if energy is None or energy < threshold:
            continue
        previous = signals.energy[index - 1] if index else None
        nxt = signals.energy[index + 1] if index + 1 < len(signals.energy) else None
        if previous is not None and energy < previous:
            continue
        if nxt is not None and energy < nxt:
            continue
        peaks.append(MotionCandidate(signals.timestamps_ms[index], energy))
    return peaks
