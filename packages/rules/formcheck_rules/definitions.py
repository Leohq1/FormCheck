from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from formcheck_biomechanics.models import ViewHint

from formcheck_rules.models import CalibrationStatus, Severity


class Comparison(str, Enum):
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    enabled: bool
    calibration_status: CalibrationStatus
    required_feature: str
    supported_views: tuple[ViewHint, ...]
    minimum_confidence: float
    operator: Comparison | None
    threshold: float | None
    severity: Severity | None
    label: str
    retrieval_tags: tuple[str, ...] = ()


def compares(operator: Comparison, value: float, threshold: float) -> bool:
    if operator is Comparison.LT:
        return value < threshold
    if operator is Comparison.LTE:
        return value <= threshold
    if operator is Comparison.GT:
        return value > threshold
    return value >= threshold
