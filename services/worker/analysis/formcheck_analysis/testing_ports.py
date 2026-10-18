"""PROVISIONAL: requires Person 2 approval. Local adapters for tests only."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from formcheck_analysis.ports import AnalysisStage, ArtifactMetadata, CancellationError


@dataclass
class ProgressEvent:
    analysis_id: UUID
    stage: AnalysisStage
    progress: float | None
    message_key: str


class LocalArtifactStore:
    """PROVISIONAL: requires Person 2 approval."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._objects: dict[str, Path] = {}

    def add_source(self, object_key: str, file_path: Path) -> None:
        self._objects[object_key] = file_path

    def materialize(self, object_key: str) -> Path:
        path = self._objects.get(object_key)
        if path is None or not path.is_file():
            raise FileNotFoundError(object_key)
        return path

    def put_file(self, object_key: str, local_path: Path, *, content_type: str) -> ArtifactMetadata:
        destination = self.root / object_key.replace("/", "__")
        if destination.exists() and destination.read_bytes() == local_path.read_bytes():
            digest = hashlib.sha256(destination.read_bytes()).hexdigest()
            return ArtifactMetadata(
                object_key=object_key,
                byte_size=destination.stat().st_size,
                content_type=content_type,
                content_sha256=digest,
            )
        shutil.copyfile(local_path, destination)
        self._objects[object_key] = destination
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        return ArtifactMetadata(
            object_key=object_key,
            byte_size=destination.stat().st_size,
            content_type=content_type,
            content_sha256=digest,
        )


class InMemoryProgress:
    """PROVISIONAL: requires Person 2 approval."""

    def __init__(self) -> None:
        self.events: list[ProgressEvent] = []

    def report(
        self,
        analysis_id: UUID,
        stage: AnalysisStage,
        progress: float | None,
        message_key: str,
    ) -> None:
        self.events.append(ProgressEvent(analysis_id, stage, progress, message_key))


class ExplicitCancellation:
    """PROVISIONAL: requires Person 2 approval."""

    def __init__(self) -> None:
        self.cancelled = False

    def raise_if_cancelled(self, analysis_id: UUID) -> None:
        if self.cancelled:
            raise CancellationError(analysis_id)
