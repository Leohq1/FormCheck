from pathlib import Path
from uuid import uuid4

import pytest
from formcheck_analysis.ports import AnalysisStage, ArtifactMetadata, CancellationError
from formcheck_analysis.testing_ports import (
    ExplicitCancellation,
    InMemoryProgress,
    LocalArtifactStore,
)


def test_local_store_uses_logical_keys_and_repeat_writes_match(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path / "objects")
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"video-bytes")
    key = "analyses/demo/source/clip.mp4"
    store.add_source(key, source)

    assert store.materialize(key) == source
    first = store.put_file("analyses/demo/normalized/video.mp4", source, content_type="video/mp4")
    second = store.put_file("analyses/demo/normalized/video.mp4", source, content_type="video/mp4")

    assert isinstance(first, ArtifactMetadata)
    assert first.object_key == "analyses/demo/normalized/video.mp4"
    assert first.content_sha256 == second.content_sha256
    assert first.byte_size == second.byte_size
    assert (tmp_path / "objects" / "analyses__demo__normalized__video.mp4").read_bytes() == b"video-bytes"


def test_progress_preserves_order_and_cancellation_is_typed() -> None:
    progress = InMemoryProgress()
    analysis_id = uuid4()
    progress.report(analysis_id, AnalysisStage.MATERIALIZE, None, "source_materialized")
    progress.report(analysis_id, AnalysisStage.NORMALIZE, 0.4, "preprocessing_completed")

    assert [event.message_key for event in progress.events] == [
        "source_materialized",
        "preprocessing_completed",
    ]
    cancellation = ExplicitCancellation()
    cancellation.raise_if_cancelled(analysis_id)
    cancellation.cancelled = True
    with pytest.raises(CancellationError):
        cancellation.raise_if_cancelled(analysis_id)
