import json
import math
from pathlib import Path

import pytest
from formcheck_analysis.models import AnalysisFindings
from formcheck_biomechanics.models import FeatureValue, QualityDisposition, QualityReport
from formcheck_rules.models import Finding
from pydantic import ValidationError

FIXTURE = Path(__file__).parent / "fixtures" / "analysis_findings_no_findings.json"


def _draft() -> AnalysisFindings:
    return AnalysisFindings.model_validate_json(FIXTURE.read_text(encoding="utf-8"))


def test_production_dump_omits_diagnostics() -> None:
    dumped = _draft().to_production_dict()

    assert dumped["schema_version"] == "0-draft"
    assert dumped["findings"] == []
    assert "diagnostics" not in dumped


def test_development_dump_includes_diagnostics() -> None:
    dumped = _draft().to_development_dict()

    assert dumped["diagnostics"]["candidate_rule_evaluations"][0]["evaluation"] == "would_trigger"
    assert dumped["diagnostics"]["candidate_rule_evaluations"][0]["enabled"] is False


def test_no_findings_fixture_round_trips() -> None:
    original = json.loads(FIXTURE.read_text(encoding="utf-8"))
    restored = json.loads(_draft().model_dump_json())

    assert restored == original


def test_non_finite_feature_value_fails_validation() -> None:
    with pytest.raises(ValidationError):
        FeatureValue(
            name="dominant_elbow_angle_at_max_wrist_height_deg",
            value=math.inf,
            unit="deg",
            confidence=0.5,
            available=True,
            feature_version="1",
        )


def test_ineligible_analysis_validates_without_phase_data() -> None:
    findings = AnalysisFindings(
        analysis_id="11111111-1111-4111-8111-111111111111",
        quality=QualityReport(
            overall=None,
            eligible=False,
            disposition=QualityDisposition.INELIGIBLE,
            warnings=["body_not_fully_visible"],
            remediation=["Keep the full body in frame."],
        ),
        features=[],
        findings=[],
        versions={
            "pipeline": "2026.10.0",
            "pose_estimator": "mediapipe-pose-landmarker",
            "feature_schema": "1",
            "rule_set": "clear.low_arm_extension.v1",
        },
    )

    assert findings.stroke is None
    assert findings.phases is None
    assert findings.findings == []


def test_public_finding_type_is_separate_from_draft_payload() -> None:
    dumped = _draft().to_production_dict()
    for item in dumped["findings"]:
        Finding.model_validate(item)
