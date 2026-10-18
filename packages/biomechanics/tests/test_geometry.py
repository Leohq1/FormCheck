from __future__ import annotations

import math

from formcheck_biomechanics.geometry import joint_angle_deg
from hypothesis import given
from hypothesis import strategies as st


def test_known_right_and_straight_angles() -> None:
    assert joint_angle_deg((1.0, 0.0), (0.0, 0.0), (0.0, 1.0)) == 90
    assert joint_angle_deg((1.0, 0.0), (0.0, 0.0), (-1.0, 0.0)) == 180


def test_degenerate_or_missing_points_are_unavailable() -> None:
    assert joint_angle_deg((0.0, 0.0), (0.0, 0.0), (1.0, 0.0)) is None
    assert joint_angle_deg(None, (0.0, 0.0), (1.0, 0.0)) is None
    assert joint_angle_deg((math.nan, 0.0), (0.0, 0.0), (1.0, 0.0)) is None


@given(
    points=st.lists(st.floats(min_value=-20, max_value=20, allow_nan=False, allow_infinity=False), min_size=6, max_size=6),
    shift=st.floats(min_value=-50, max_value=50, allow_nan=False, allow_infinity=False),
    scale=st.floats(min_value=0.2, max_value=5, allow_nan=False, allow_infinity=False),
)
def test_angle_is_invariant_to_translation_and_uniform_scale(points: list[float], shift: float, scale: float) -> None:
    start = (points[0], points[1])
    vertex = (points[2], points[3])
    end = (points[4], points[5])
    original = joint_angle_deg(start, vertex, end)
    moved = joint_angle_deg(
        (start[0] * scale + shift, start[1] * scale + shift),
        (vertex[0] * scale + shift, vertex[1] * scale + shift),
        (end[0] * scale + shift, end[1] * scale + shift),
    )
    if original is None:
        assert moved is None
    else:
        assert moved is not None
        assert abs(moved - original) < 1e-4
