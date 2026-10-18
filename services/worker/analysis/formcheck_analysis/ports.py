"""PROVISIONAL: requires Person 2 approval.

These ports describe analysis needs only. They do not choose storage, retry,
authentication, or retention behavior.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalysisStage(str, Enum):
    MATERIALIZE = "materialize"
    INSPECT = "inspect"
    NORMALIZE = "normalize"
    POSE = "pose"
    QUALITY = "quality"
    SEGMENT = "segment"
    PHASES = "phases"
    FEATURES = "features"
    RULES = "rules"
    ASSEMBLE = "assemble"


class ArtifactMetadata(BaseModel):
    """Integration-neutral facts. No signed URLs or storage-specific fields."""

    model_config = ConfigDict(extra="forbid")

    object_key: str
    byte_size: int
    content_type: str
    content_sha256: str


class CancellationError(Exception):
    def __init__(self, analysis_id: UUID) -> None:
        super().__init__("Analysis was cancelled.")
        self.analysis_id = analysis_id
        self.safe_message = "Analysis was cancelled."


class ArtifactReader(Protocol):
    def materialize(self, object_key: str) -> Path: ...


class ArtifactWriter(Protocol):
    def put_file(self, object_key: str, local_path: Path, *, content_type: str) -> ArtifactMetadata: ...


class CancellationPort(Protocol):
    def raise_if_cancelled(self, analysis_id: UUID) -> None: ...


class ProgressPort(Protocol):
    def report(
        self,
        analysis_id: UUID,
        stage: AnalysisStage,
        progress: float | None,
        message_key: str,
    ) -> None: ...
