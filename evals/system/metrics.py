"""End-to-end bookkeeping for one analysis."""

from __future__ import annotations


def completion_rate(statuses: list[str]) -> float:
    if not statuses:
        return 0.0
    finished = sum(1 for status in statuses if status in {"completed", "inconclusive", "failed"})
    return finished / len(statuses)
