"""Planar joint geometry. Image y grows downward; height is the negated y."""

from __future__ import annotations

import math
from typing import Sequence


Point = Sequence[float]


def elbow_angle_deg(shoulder: Point, elbow: Point, wrist: Point) -> float:
    """Return the interior angle at the elbow, in degrees."""
    upper = (shoulder[0] - elbow[0], shoulder[1] - elbow[1])
    forearm = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    return _angle_between(upper, forearm)


def _angle_between(left: tuple[float, float], right: tuple[float, float]) -> float:
    dot = left[0] * right[0] + left[1] * right[1]
    left_len = math.hypot(*left)
    right_len = math.hypot(*right)
    if left_len == 0 or right_len == 0:
        raise ValueError("A joint segment has zero length.")
    cosine = max(-1.0, min(1.0, dot / (left_len * right_len)))
    return math.degrees(math.acos(cosine))
