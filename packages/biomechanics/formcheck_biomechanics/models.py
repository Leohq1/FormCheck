from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Handedness(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class ViewHint(str, Enum):
    SIDE = "side"
    REAR_THREE_QUARTER = "rear_three_quarter"


class QualityDisposition(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    INCONCLUSIVE = "inconclusive"


class PhaseName(str, Enum):
    PREPARATION = "preparation"
    LOADING = "loading"
    ACCELERATION = "acceleration"
    CONTACT = "contact"
    FOLLOW_THROUGH = "follow_through"


class QualityComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    detail: str = ""


class QualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    eligible: bool
    disposition: QualityDisposition
    warnings: list[str] = Field(default_factory=list)
    remediation: list[str] = Field(default_factory=list)
    components: list[QualityComponent] = Field(default_factory=list)
    version: str = "quality.v1-provisional"


class StrokeWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stroke: str = "overhead_clear"
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def window_is_ordered(self) -> Self:
        if self.end_ms < self.start_ms:
            raise ValueError("stroke end must not precede the start")
        return self


class PhaseEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: PhaseName
    start_ms: int | None = Field(default=None, ge=0)
    end_ms: int | None = Field(default=None, ge=0)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    uncertainty: float = Field(ge=0, le=1, allow_inf_nan=False)
    available: bool
    unavailable_reason: str | None = None
    evidence: list[str] = Field(default_factory=list)


class PhaseSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phases: list[PhaseEstimate]
    contact_available: bool
    version: str = "phases.v1-provisional"


class FeatureValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: float | None = Field(default=None, allow_inf_nan=False)
    unit: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    available: bool
    feature_version: str
    unavailable_reason: str | None = None

    @model_validator(mode="after")
    def availability_matches_value(self) -> Self:
        if self.available:
            if self.value is None or not self.unit or not self.feature_version:
                raise ValueError("available feature requires value, unit, and version")
        elif self.value is not None:
            raise ValueError("unavailable feature cannot have a value")
        return self
