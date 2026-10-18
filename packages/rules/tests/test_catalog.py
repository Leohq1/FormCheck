from formcheck_biomechanics.models import ViewHint
from formcheck_rules.catalog import (
    DEVELOPMENT_LOW_ARM_EXTENSION_THRESHOLD_DEG,
    LOW_ARM_EXTENSION,
    PROVISIONAL_TEST_ONLY,
)


def test_arm_extension_candidate_is_disabled_and_uncalibrated() -> None:
    rule = LOW_ARM_EXTENSION

    assert rule.rule_id == "clear.low_arm_extension.v1"
    assert rule.enabled is False
    assert rule.calibration_status.value == "not_calibrated"
    assert rule.threshold is None
    assert rule.severity is None
    assert rule.operator is None
    assert rule.required_feature == "dominant_elbow_angle_at_max_wrist_height_deg"
    assert set(rule.supported_views) == {ViewHint.SIDE, ViewHint.REAR_THREE_QUARTER}
    assert "overhead_clear" in rule.retrieval_tags
    assert DEVELOPMENT_LOW_ARM_EXTENSION_THRESHOLD_DEG == 140.0
    assert PROVISIONAL_TEST_ONLY == "provisional_test_only"
