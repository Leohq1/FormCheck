"""Storage and progress adapters for the provisional analysis pipeline."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


PUBLIC_STAGE = {
    "materialize": "preprocessing",
    "inspect": "preprocessing",
    "normalize": "preprocessing",
    "pose": "pose_estimation",
    "quality": "phase_detection",
    "segment": "phase_detection",
    "phases": "phase_detection",
    "features": "rule_evaluation",
    "rules": "rule_evaluation",
    "assemble": "generating",
}


class _DownloadUpload(Protocol):
    def download_file(self, key: str, destination: Path) -> None: ...

    def upload_file(self, key: str, source: Path, *, content_type: str) -> None: ...


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    byte_size: int
    content_type: str
    content_sha256: str


class ObjectStorageArtifacts:
    def __init__(self, storage: _DownloadUpload, workdir: Path) -> None:
        self._storage = storage
        self._workdir = workdir
        self._workdir.mkdir(parents=True, exist_ok=True)

    def materialize(self, object_key: str) -> Path:
        destination = self._workdir / "source.bin"
        self._storage.download_file(object_key, destination)
        if not destination.is_file():
            raise FileNotFoundError(object_key)
        return destination

    def put_file(self, object_key: str, local_path: Path, *, content_type: str) -> StoredObject:
        self._storage.upload_file(object_key, local_path, content_type=content_type)
        digest = hashlib.sha256(local_path.read_bytes()).hexdigest()
        return StoredObject(
            object_key=object_key,
            byte_size=local_path.stat().st_size,
            content_type=content_type,
            content_sha256=digest,
        )


class StageProgress:
    def __init__(self, report: Callable[[str, str | None, float | None], None]) -> None:
        self._report = report

    def report(self, analysis_id: Any, stage: Any, progress: float | None, message_key: str) -> None:
        del analysis_id
        name = getattr(stage, "value", stage)
        public = PUBLIC_STAGE.get(str(name))
        if public is None:
            return
        self._report(public, message_key, progress)
