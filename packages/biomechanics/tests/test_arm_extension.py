import math

from formcheck_biomechanics.features.arm_extension import (
    JointSample,
    dominant_elbow_angle_at_max_wrist_height,
)
from formcheck_biomechanics.geometry import elbow_angle_deg


def _sample(height: float, confidence: float = 0.9, elbow=(0.0, 0.0)) -> JointSample:
    return JointSample(
        timestamp_ms=int(height * 10),
        wrist_height=height,
        shoulder=(0.0, 1.0),
        elbow=elbow,
        wrist=(1.0, 0.0),
        confidence=confidence,
    )


def test_right_angle_at_the_highest_wrist():
    feature = dominant_elbow_angle_at_max_wrist_height([_sample(1.0), _sample(3.0), _sample(2.0)])

    assert feature.available
    assert feature.unit == "deg"
    assert feature.value == 90.0
    assert feature.name == "dominant_elbow_angle_at_max_wrist_height_deg"


def test_straight_arm_is_180_degrees():
    angle = elbow_angle_deg((0.0, 1.0), (0.0, 0.0), (0.0, -1.0))
    assert math.isclose(angle, 180.0)


def test_low_confidence_neighbor_rejects_the_peak():
    feature = dominant_elbow_angle_at_max_wrist_height(
        [_sample(1.0), _sample(3.0, confidence=0.2), _sample(2.0)]
    )

    assert feature.available is False
    assert feature.value is None
    assert feature.reason == "unstable_or_unreliable_maximum"
