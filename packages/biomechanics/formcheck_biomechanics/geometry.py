"""Planar joint geometry. Image y grows downward; height is the negated y."""

from __future__ import annotations

import math
from collections.abc import Sequence

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


def joint_angle_deg(
    start: Point | None,
    vertex: Point | None,
    end: Point | None,
) -> float | None:
    """Planar angle at ``vertex``. Missing or degenerate points stay unavailable."""
    if start is None or vertex is None or end is None:
        return None
    if len(start) < 2 or len(vertex) < 2 or len(end) < 2:
        return None
    values = (start[0], start[1], vertex[0], vertex[1], end[0], end[1])
    if not all(math.isfinite(value) for value in values):
        return None
    first = (start[0] - vertex[0], start[1] - vertex[1])
    second = (end[0] - vertex[0], end[1] - vertex[1])
    first_length = math.hypot(*first)
    second_length = math.hypot(*second)
    if first_length <= 1e-9 or second_length <= 1e-9:
        return None
    cosine = (first[0] * second[0] + first[1] * second[1]) / (first_length * second_length)
    if cosine > 1.0 or cosine < -1.0:
        if abs(cosine) - 1.0 <= 1e-6:
            cosine = math.copysign(1.0, cosine)
        else:
            return None
    return math.degrees(math.acos(cosine))
