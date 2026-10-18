from __future__ import annotations

from typing import cast

from formcheck_biomechanics.models import (
    FeatureValue,
    Handedness,
    PhaseSet,
    QualityReport,
    StrokeWindow,
    ViewHint,
)
from formcheck_rules.models import CandidateRuleEvaluation, Finding
from pydantic import BaseModel, ConfigDict, Field

__all__ = ["AnalysisFindings", "Handedness", "ViewHint"]


class VersionInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pipeline: str
    pose_estimator: str
    feature_schema: str
    rule_set: str


class AnalysisDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_rule_evaluations: list[CandidateRuleEvaluation] = Field(default_factory=list)


class AnalysisFindings(BaseModel):
    """Internal draft result. Production serialization never includes diagnostics."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0-draft"
    analysis_id: str
    quality: QualityReport
    stroke: StrokeWindow | None = None
    phases: PhaseSet | None = None
    features: list[FeatureValue] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    versions: VersionInfo
    diagnostics: AnalysisDiagnostics | None = None
    handedness: Handedness | None = None
    view_hint: ViewHint | None = None

    def to_production_dict(self) -> dict[str, object]:
        raw = self.model_dump(mode="json", exclude={"diagnostics"})
        raw.pop("diagnostics", None)
        return cast(dict[str, object], raw)

    def to_development_dict(self) -> dict[str, object]:
        return cast(dict[str, object], self.model_dump(mode="json"))
