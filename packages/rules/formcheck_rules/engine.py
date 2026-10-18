"""Deterministic rules. The first clear rule stays out of production findings."""

from __future__ import annotations

from dataclasses import dataclass

from formcheck_biomechanics.features.arm_extension import FEATURE_NAME, FeatureValue

RULE_ID = "clear.low_arm_extension.v1"
RULE_LABEL = "Low arm extension at maximum reach"
DEVELOPMENT_THRESHOLD_DEG = 140.0
CALIBRATION = "not_calibrated"
ENABLED = False


@dataclass(frozen=True)
class Diagnostic:
    rule_id: str
    evaluation: str
    feature: str
    value: float | None
    threshold_deg: float
    threshold_label: str = "provisional_test_only"


@dataclass(frozen=True)
class RuleEvaluation:
    findings: tuple[dict[str, object], ...]
    diagnostics: tuple[Diagnostic, ...]


def evaluate_clear_arm_extension(
    feature: FeatureValue,
    *,
    diagnostics_enabled: bool = False,
) -> RuleEvaluation:
    """Production findings stay empty until coach-labeled precision is at least 0.80."""
    diagnostic = _diagnostic(feature) if diagnostics_enabled else None
    return RuleEvaluation(
        findings=(),
        diagnostics=(diagnostic,) if diagnostic is not None else (),
    )


def production_findings(result: RuleEvaluation) -> tuple[dict[str, object], ...]:
    return result.findings


def _diagnostic(feature: FeatureValue) -> Diagnostic:
    if not feature.available or feature.value is None:
        evaluation = "inconclusive"
    elif feature.value < DEVELOPMENT_THRESHOLD_DEG:
        evaluation = "would_trigger"
    else:
        evaluation = "would_pass"
    return Diagnostic(
        rule_id=RULE_ID,
        evaluation=evaluation,
        feature=FEATURE_NAME,
        value=feature.value,
        threshold_deg=DEVELOPMENT_THRESHOLD_DEG,
    )
