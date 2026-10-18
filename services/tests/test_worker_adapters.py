from pathlib import Path

from formcheck.worker.adapters import PUBLIC_STAGE, ObjectStorageArtifacts, StageProgress


class _MemoryStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def download_file(self, key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.files[key])

    def upload_file(self, key: str, source: Path, *, content_type: str) -> None:
        del content_type
        self.files[key] = source.read_bytes()


def test_object_round_trip_keeps_bytes_and_hash(tmp_path: Path) -> None:
    storage = _MemoryStorage()
    storage.files["analyses/a/source/clip.mp4"] = b"video-bytes"
    artifacts = ObjectStorageArtifacts(storage, tmp_path)

    local = artifacts.materialize("analyses/a/source/clip.mp4")
    stored = artifacts.put_file("analyses/a/normalized/video.mp4", local, content_type="video/mp4")

    assert local.read_bytes() == b"video-bytes"
    assert storage.files["analyses/a/normalized/video.mp4"] == b"video-bytes"
    assert stored.content_sha256
    assert stored.byte_size == len(b"video-bytes")


def test_pipeline_stages_map_onto_public_progress() -> None:
    seen: list[tuple[str, str]] = []
    progress = StageProgress(lambda stage, message_key, progress_value: seen.append((stage, message_key)))

    class _Stage:
        value = "normalize"

    progress.report(None, _Stage(), None, "preprocessing_completed")

    assert PUBLIC_STAGE["pose"] == "pose_estimation"
    assert seen == [("preprocessing", "preprocessing_completed")]
