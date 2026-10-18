from __future__ import annotations

from dataclasses import dataclass

from formcheck_biomechanics.features.arm_extension import FeatureValue as SampleFeatureValue
from formcheck_biomechanics.models import FeatureValue, ViewHint

from formcheck_rules.catalog import (
    DEVELOPMENT_LOW_ARM_EXTENSION_THRESHOLD_DEG,
    LOW_ARM_EXTENSION_RULE_ID,
    PROVISIONAL_TEST_ONLY,
)
from formcheck_rules.definitions import Comparison, RuleDefinition, compares
from formcheck_rules.models import (
    CalibrationStatus,
    CandidateRuleEvaluation,
    DiagnosticOutcome,
    Evidence,
    Finding,
    ProductionOutcome,
)

CANDIDATE_MESSAGE = "Candidate evaluation only; not a validated technique finding."


@dataclass(frozen=True)
class RuleContext:
    view: ViewHint | None


@dataclass(frozen=True)
class ProductionEvaluation:
    rule_id: str
    outcome: ProductionOutcome
    finding: Finding | None = None


@dataclass(frozen=True)
class RuleEvaluationResult:
    production: tuple[ProductionEvaluation, ...]
    diagnostics: tuple[CandidateRuleEvaluation, ...]


@dataclass(frozen=True)
class DevelopmentEvaluationConfig:
    """Plumbing-only threshold. It is not a production or calibrated cutoff."""

    low_arm_extension_threshold_deg: float = DEVELOPMENT_LOW_ARM_EXTENSION_THRESHOLD_DEG
    label: str = PROVISIONAL_TEST_ONLY


class RuleEngine:
    def __init__(
        self,
        rules: tuple[RuleDefinition, ...],
        *,
        development: DevelopmentEvaluationConfig | None = None,
    ) -> None:
        self.rules = tuple(sorted(rules, key=lambda item: item.rule_id))
        self.development = development or DevelopmentEvaluationConfig()

    def evaluate(
        self,
        features: tuple[FeatureValue, ...] | list[FeatureValue],
        context: RuleContext,
        *,
        diagnostics_enabled: bool,
    ) -> RuleEvaluationResult:
        by_name = {feature.name: feature for feature in features}
        production: list[ProductionEvaluation] = []
        diagnostics: list[CandidateRuleEvaluation] = []
        for rule in self.rules:
            feature = by_name.get(rule.required_feature)
            if rule.enabled and rule.calibration_status is CalibrationStatus.CALIBRATED:
                production.append(_production(rule, feature, context))
            elif diagnostics_enabled:
                diagnostics.append(_diagnostic(rule, feature, context, self.development))
        return RuleEvaluationResult(tuple(production), tuple(diagnostics))


def _production(rule: RuleDefinition, feature: FeatureValue | None, context: RuleContext) -> ProductionEvaluation:
    outcome, evidence = _measure(rule, feature, context, rule.operator, rule.threshold)
    if outcome is ProductionOutcome.FINDING:
        if rule.severity is None or evidence is None:
            return ProductionEvaluation(rule.rule_id, ProductionOutcome.INCONCLUSIVE)
        return ProductionEvaluation(
            rule.rule_id,
            ProductionOutcome.FINDING,
            Finding(
                rule_id=rule.rule_id,
                label=rule.label,
                severity=rule.severity,
                confidence=feature.confidence or 0.0,  # type: ignore[union-attr]
                evidence=[evidence],
                retrieval_tags=list(rule.retrieval_tags),
            ),
        )
    return ProductionEvaluation(rule.rule_id, outcome)


def _diagnostic(
    rule: RuleDefinition,
    feature: FeatureValue | None,
    context: RuleContext,
    development: DevelopmentEvaluationConfig,
) -> CandidateRuleEvaluation:
    operator = Comparison.LT
    threshold = (
        development.low_arm_extension_threshold_deg
        if rule.rule_id == LOW_ARM_EXTENSION_RULE_ID
        else rule.threshold
    )
    outcome, _evidence = _measure(rule, feature, context, operator, threshold)
    mapped = {
        ProductionOutcome.FINDING: DiagnosticOutcome.WOULD_TRIGGER,
        ProductionOutcome.PASS: DiagnosticOutcome.WOULD_PASS,
        ProductionOutcome.NOT_APPLICABLE: DiagnosticOutcome.NOT_APPLICABLE,
        ProductionOutcome.INCONCLUSIVE: DiagnosticOutcome.INCONCLUSIVE,
    }[outcome]
    return CandidateRuleEvaluation(
        rule_id=rule.rule_id,
        enabled=rule.enabled,
        calibration_status=rule.calibration_status,
        evaluation=mapped,
        message=CANDIDATE_MESSAGE,
    )


def _measure(
    rule: RuleDefinition,
    feature: FeatureValue | None,
    context: RuleContext,
    operator: Comparison | None,
    threshold: float | None,
) -> tuple[ProductionOutcome, Evidence | None]:
    if context.view not in rule.supported_views or feature is None:
        return ProductionOutcome.NOT_APPLICABLE, None
    if not feature.available or feature.value is None or feature.confidence is None:
        return ProductionOutcome.INCONCLUSIVE, None
    if feature.confidence < rule.minimum_confidence or operator is None or threshold is None:
        return ProductionOutcome.INCONCLUSIVE, None
    evidence = Evidence(
        feature=feature.name,
        value=feature.value,
        unit=feature.unit or "",
        feature_version=feature.feature_version,
    )
    if compares(operator, feature.value, threshold):
        return ProductionOutcome.FINDING, evidence
    return ProductionOutcome.PASS, evidence


# Sample-level API used by the coaching integration. Production findings stay empty.
RULE_ID = LOW_ARM_EXTENSION_RULE_ID
RULE_LABEL = "Low arm extension at maximum reach"
DEVELOPMENT_THRESHOLD_DEG = DEVELOPMENT_LOW_ARM_EXTENSION_THRESHOLD_DEG
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
    feature: SampleFeatureValue,
    *,
    diagnostics_enabled: bool = False,
) -> RuleEvaluation:
    """Production findings stay empty. The candidate rule is not calibrated."""
    diagnostic = _sample_diagnostic(feature) if diagnostics_enabled else None
    return RuleEvaluation(findings=(), diagnostics=(diagnostic,) if diagnostic is not None else ())


def production_findings(result: RuleEvaluation) -> tuple[dict[str, object], ...]:
    return result.findings


def _sample_diagnostic(feature: SampleFeatureValue) -> Diagnostic:
    if not feature.available or feature.value is None:
        evaluation = "inconclusive"
    elif feature.value < DEVELOPMENT_THRESHOLD_DEG:
        evaluation = "would_trigger"
    else:
        evaluation = "would_pass"
    return Diagnostic(
        rule_id=RULE_ID,
        evaluation=evaluation,
        feature=feature.name,
        value=feature.value,
        threshold_deg=DEVELOPMENT_THRESHOLD_DEG,
    )
