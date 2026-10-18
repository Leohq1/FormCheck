import pytest
from formcheck_rules.models import (
    CalibrationStatus,
    CandidateRuleEvaluation,
    DiagnosticOutcome,
    Finding,
    Severity,
)
from pydantic import ValidationError


def test_candidate_diagnostic_cannot_validate_as_finding() -> None:
    diagnostic = CandidateRuleEvaluation(
        rule_id="clear.low_arm_extension.v1",
        enabled=False,
        calibration_status=CalibrationStatus.NOT_CALIBRATED,
        evaluation=DiagnosticOutcome.WOULD_TRIGGER,
        message="Candidate evaluation only; not a validated technique finding.",
    )

    with pytest.raises(ValidationError):
        Finding.model_validate(diagnostic.model_dump())


def test_finding_uses_public_severity() -> None:
    finding = Finding(
        rule_id="test.calibrated.v1",
        label="Test finding",
        severity=Severity.MODERATE,
        confidence=0.8,
        evidence=[],
    )

    assert finding.severity is Severity.MODERATE
