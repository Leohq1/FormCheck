from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


class ProductionOutcome(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    PASS = "pass"
    FINDING = "finding"
    INCONCLUSIVE = "inconclusive"


class DiagnosticOutcome(str, Enum):
    WOULD_TRIGGER = "would_trigger"
    WOULD_PASS = "would_pass"
    NOT_APPLICABLE = "not_applicable"
    INCONCLUSIVE = "inconclusive"


class CalibrationStatus(str, Enum):
    NOT_CALIBRATED = "not_calibrated"
    CALIBRATED = "calibrated"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature: str
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1)
    feature_version: str = Field(min_length=1)


class Finding(BaseModel):
    """A supported technique result. Candidate diagnostics are a different type."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str
    label: str
    severity: Severity
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    evidence: list[Evidence] = Field(default_factory=list)
    retrieval_tags: list[str] = Field(default_factory=list)


class CandidateRuleEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    enabled: bool
    calibration_status: CalibrationStatus
    evaluation: DiagnosticOutcome
    message: str
