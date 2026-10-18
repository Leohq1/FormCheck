from __future__ import annotations

from formcheck_rules.engine import ProductionEvaluation, RuleEvaluationResult
from formcheck_rules.models import Finding, ProductionOutcome


def production_findings(result: RuleEvaluationResult) -> tuple[Finding, ...]:
    return tuple(
        item.finding
        for item in result.production
        if item.outcome is ProductionOutcome.FINDING and item.finding is not None
    )


def assemble_production_json(result: RuleEvaluationResult) -> dict[str, object]:
    """Build public rule output. This function accepts no diagnostic argument."""
    return {
        "schema_version": "0-draft",
        "findings": [item.model_dump(mode="json") for item in production_findings(result)],
    }


def production_only(evaluations: tuple[ProductionEvaluation, ...]) -> tuple[Finding, ...]:
    return production_findings(RuleEvaluationResult(evaluations, ()))
