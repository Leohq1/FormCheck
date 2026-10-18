from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    feature: str
    value: float | int | str | None = None
    unit: str = ""
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    available: bool = True


class FeatureMeasurement(BaseModel):
    """Measured context. A feature value is not a technique finding."""

    name: str
    value: float | int | str | None = None
    unit: str = ""
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    available: bool = True
    feature_version: str | None = None


class Finding(BaseModel):
    rule_id: str
    label: str
    severity: str = Field(pattern="^(low|medium|moderate|high|minor|major)$")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    retrieval_tags: list[str] = Field(default_factory=list)


class AnalysisFindings(BaseModel):
    """Provisional Person 3 handoff.

    schema_version "0-draft" is accepted for local development. It is not the
    shared contract until analysis-findings.schema.json is approved.
    Extra fields, including candidate-rule diagnostics, are ignored.
    """

    model_config = ConfigDict(extra="ignore")

    schema_version: str = "0-draft"
    analysis_id: str
    quality: dict = Field(default_factory=dict)
    stroke: dict = Field(default_factory=dict)
    features: list[FeatureMeasurement] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    versions: dict = Field(default_factory=dict)
