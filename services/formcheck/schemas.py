"""HTTP + job schemas aligned with packages/contracts (Milestone A)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

StrokeId = Literal["overhead_clear", "smash", "drop"]
Handedness = Literal["left", "right"]
ViewHint = Literal["side", "rear_three_quarter"]
FindingSeverity = Literal["minor", "moderate", "major"]

AnalysisStatus = Literal[
    "created",
    "uploading",
    "queued",
    "preprocessing",
    "pose_estimation",
    "phase_detection",
    "rule_evaluation",
    "retrieval",
    "generating",
    "completed",
    "inconclusive",
    "failed",
    "cancelled",
    "expired",
    "deleted",
]

ProgressStage = Literal[
    "created",
    "uploading",
    "queued",
    "preprocessing",
    "pose_estimation",
    "phase_detection",
    "rule_evaluation",
    "retrieval",
    "generating",
    "completed",
    "inconclusive",
    "failed",
    "cancelled",
    "expired",
]

TERMINAL_STATUSES = frozenset(
    {"completed", "inconclusive", "failed", "cancelled", "expired", "deleted"}
)

RESULT_READY_STATUSES = frozenset({"completed", "inconclusive", "failed", "expired"})


# --- Public create / upload (frontend request aliases retained) ---


class CreateAnalysisRequest(BaseModel):
    stroke: StrokeId
    handedness: Handedness
    view_hint: ViewHint
    consent: bool
    filename: str = Field(min_length=1, max_length=512)
    content_type: str
    byte_size: int = Field(gt=0)

    @field_validator("stroke", mode="before")
    @classmethod
    def accept_frontend_clear_id(cls, value: object) -> object:
        """The upload form uses clear. Jobs and findings use overhead_clear."""
        if value == "clear":
            return "overhead_clear"
        return value


class CreateAnalysisResponse(BaseModel):
    schema_version: str
    analysis_id: str
    capability_token: str
    upload_url: str
    status: AnalysisStatus


class CompleteUploadResponse(BaseModel):
    schema_version: str
    analysis_id: str
    status: AnalysisStatus


# --- Worker job (analysis-job.schema.json) ---


class AnalysisJob(BaseModel):
    schema_version: Literal["1"] = "1"
    analysis_id: str
    video_object_key: str
    stroke: StrokeId
    handedness: Handedness
    view_hint: ViewHint
    pipeline_version: str


# --- Progress (analysis-progress.schema.json + API enrichment) ---


class AnalysisProgressEvent(BaseModel):
    """Exact worker progress event (packages/contracts/analysis-progress.schema.json)."""

    schema_version: Literal["1"] = "1"
    analysis_id: str
    stage: ProgressStage
    progress: float | None
    message_key: str | None
    updated_at: str


class AnalysisProgress(BaseModel):
    """HTTP poll payload: contract progress fields plus status/expires_at for clients."""

    schema_version: str
    analysis_id: str
    status: AnalysisStatus
    stage: ProgressStage | str | None
    progress: float | None
    message_key: str | None
    updated_at: str
    expires_at: str | None


# --- Result (analysis-result.schema.json) ---


class EvidenceItem(BaseModel):
    feature: str
    value: float
    unit: str


class AnalysisFinding(BaseModel):
    rule_id: str
    label: str
    severity: FindingSeverity
    confidence: float
    evidence: list[EvidenceItem]
    retrieval_tags: list[str]


class QualityReport(BaseModel):
    overall: float = Field(ge=0, le=1)
    warnings: list[str]


class StrokeInfo(BaseModel):
    type: StrokeId
    start_time_ms: int | None = None
    end_time_ms: int | None = None
    contact_time_ms: int | None = None
    confidence: float | None = None


class Citation(BaseModel):
    source_id: str
    chunk_id: str
    locator: str


class FeedbackTip(BaseModel):
    finding_id: str
    title: str
    explanation: str
    practice_cue: str
    citations: list[Citation]


class Feedback(BaseModel):
    summary: str
    tips: list[FeedbackTip]
    limitations: list[str]
    model: str
    prompt_version: str


class AnalysisError(BaseModel):
    code: str
    safe_message: str
    retryable: bool
    remediation: list[str]
    correlation_id: str
    details: dict[str, Any] | None = None


class AnalysisResult(BaseModel):
    schema_version: Literal["1"] = "1"
    analysis_id: str
    status: Literal["completed", "inconclusive", "failed", "expired", "cancelled"]
    quality: QualityReport
    stroke: StrokeInfo
    findings: list[AnalysisFinding]
    feedback: Feedback
    versions: dict[str, str]
    error: AnalysisError | None = None
    completed_at: str | None
    expires_at: str


class ApiErrorBody(BaseModel):
    error: dict[str, Any]
