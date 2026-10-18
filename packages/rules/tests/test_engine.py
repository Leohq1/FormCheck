from formcheck_biomechanics.features.arm_extension import FeatureValue
from formcheck_rules.engine import (
    ENABLED,
    RULE_ID,
    evaluate_clear_arm_extension,
    production_findings,
)


def _feature(value: float | None, available: bool = True) -> FeatureValue:
    return FeatureValue(
        name="dominant_elbow_angle_at_max_wrist_height_deg",
        version="1",
        unit="deg",
        value=value,
        confidence=0.9 if available else None,
        available=available,
    )


def test_candidate_rule_stays_disabled():
    assert ENABLED is False
    assert RULE_ID == "clear.low_arm_extension.v1"


def test_would_trigger_never_becomes_a_production_finding():
    result = evaluate_clear_arm_extension(_feature(128.0), diagnostics_enabled=True)

    assert result.diagnostics[0].evaluation == "would_trigger"
    assert production_findings(result) == ()
    assert result.findings == ()


def test_diagnostics_are_omitted_unless_requested():
    result = evaluate_clear_arm_extension(_feature(128.0), diagnostics_enabled=False)
    assert result.diagnostics == ()
