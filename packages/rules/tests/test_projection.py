import pytest
from formcheck_biomechanics.models import FeatureValue, ViewHint
from formcheck_rules.catalog import LOW_ARM_EXTENSION
from formcheck_rules.engine import RuleContext, RuleEngine
from formcheck_rules.models import DiagnosticOutcome, Finding
from formcheck_rules.projection import assemble_production_json, production_findings
from pydantic import ValidationError


def _feature(value: float) -> FeatureValue:
    return FeatureValue(
        name="dominant_elbow_angle_at_max_wrist_height_deg",
        value=value,
        unit="deg",
        confidence=0.81,
        available=True,
        feature_version="1",
    )


def test_disabled_would_trigger_never_becomes_finding() -> None:
    result = RuleEngine((LOW_ARM_EXTENSION,)).evaluate(
        [_feature(128)],
        RuleContext(view=ViewHint.SIDE),
        diagnostics_enabled=True,
    )

    assert result.diagnostics[0].evaluation is DiagnosticOutcome.WOULD_TRIGGER
    assert result.diagnostics[0].enabled is False
    assert result.diagnostics[0].calibration_status.value == "not_calibrated"
    assert production_findings(result) == ()
    assert "diagnostics" not in assemble_production_json(result)
    assert assemble_production_json(result)["findings"] == []


def test_diagnostics_are_absent_when_disabled_and_cannot_parse_as_findings() -> None:
    result = RuleEngine((LOW_ARM_EXTENSION,)).evaluate(
        [_feature(128)],
        RuleContext(view=ViewHint.SIDE),
        diagnostics_enabled=False,
    )

    assert result.diagnostics == ()
    with pytest.raises(ValidationError):
        Finding.model_validate(
            {
                "rule_id": "clear.low_arm_extension.v1",
                "enabled": False,
                "calibration_status": "not_calibrated",
                "evaluation": "would_trigger",
                "message": "Candidate evaluation only; not a validated technique finding.",
            }
        )
