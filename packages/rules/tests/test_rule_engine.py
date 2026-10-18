from formcheck_biomechanics.models import FeatureValue, ViewHint
from formcheck_rules.catalog import LOW_ARM_EXTENSION
from formcheck_rules.definitions import Comparison, RuleDefinition
from formcheck_rules.engine import RuleContext, RuleEngine
from formcheck_rules.models import CalibrationStatus, ProductionOutcome, Severity


def _rule() -> RuleDefinition:
    return RuleDefinition(
        rule_id="test.sample_angle.v1",
        enabled=True,
        calibration_status=CalibrationStatus.CALIBRATED,
        required_feature="sample_angle",
        supported_views=(ViewHint.SIDE,),
        minimum_confidence=0.6,
        operator=Comparison.LT,
        threshold=90.0,
        severity=Severity.MINOR,
        label="Sample angle",
    )


def _feature(value: float | None, confidence: float | None, *, available: bool = True) -> FeatureValue:
    return FeatureValue(
        name="sample_angle",
        value=value,
        unit="deg" if available else None,
        confidence=confidence,
        available=available,
        feature_version="1",
        unavailable_reason=None if available else "missing",
    )


def test_calibrated_rule_outcomes_are_ordered_and_gated() -> None:
    engine = RuleEngine((_rule(),))
    context = RuleContext(view=ViewHint.SIDE)

    not_applicable = engine.evaluate([], context, diagnostics_enabled=False)
    passed = engine.evaluate([_feature(100, 0.9)], context, diagnostics_enabled=False)
    finding = engine.evaluate([_feature(80, 0.9)], context, diagnostics_enabled=False)
    inconclusive = engine.evaluate([_feature(80, 0.4)], context, diagnostics_enabled=False)
    wrong_view = engine.evaluate([_feature(80, 0.9)], RuleContext(view=ViewHint.REAR_THREE_QUARTER), diagnostics_enabled=False)

    assert not_applicable.production[0].outcome is ProductionOutcome.NOT_APPLICABLE
    assert passed.production[0].outcome is ProductionOutcome.PASS
    assert finding.production[0].outcome is ProductionOutcome.FINDING
    assert finding.production[0].finding is not None
    assert finding.production[0].finding.evidence[0].feature_version == "1"
    assert inconclusive.production[0].outcome is ProductionOutcome.INCONCLUSIVE
    assert wrong_view.production[0].outcome is ProductionOutcome.NOT_APPLICABLE


def test_disabled_catalog_rule_is_not_used_as_the_test_rule() -> None:
    assert LOW_ARM_EXTENSION.enabled is False
