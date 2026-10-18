from __future__ import annotations

from fractions import Fraction

from pydantic import BaseModel, ConfigDict, Field


def parse_ffprobe_fraction(value: str) -> Fraction | None:
    text = value.strip()
    if not text or text in {"0/0", "N/A"}:
        return None
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        den = int(denominator)
        if den == 0:
            return None
        return Fraction(int(numerator), den)
    return Fraction(text)


class VideoInspection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_sha256: str
    duration_seconds: float = Field(ge=0, allow_inf_nan=False)
    byte_size: int = Field(ge=0)
    container: str
    codec: str | None
    width: int = Field(ge=0)
    height: int = Field(ge=0)
    nominal_fps: float | None = Field(default=None, allow_inf_nan=False)
    average_fps: float | None = Field(default=None, allow_inf_nan=False)
    rotation_degrees: int = 0
    stream_count: int = Field(ge=0)
    decode_ok: bool
    source_pts_ms: tuple[int, ...] = ()


class VideoEligibility(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eligible: bool
    codes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    remediation: list[str] = Field(default_factory=list)


class TimestampMapEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_index: int = Field(ge=0)
    normalized_timestamp_ms: int = Field(ge=0)
    source_timestamp_ms: int


class VideoQualitySignals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sharpness: float | None = Field(default=None, allow_inf_nan=False)
    camera_motion: float | None = Field(default=None, allow_inf_nan=False)
    available: bool
    unavailable_reason: str | None = None
    version: str


class NormalizationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_sha256: str
    timestamp_sha256: str
    output_width: int
    output_height: int
    output_fps: int
    ffmpeg_version: str
    contract_version: str = "normalization.v1"
    command: tuple[str, ...]
    timestamps: tuple[TimestampMapEntry, ...]
