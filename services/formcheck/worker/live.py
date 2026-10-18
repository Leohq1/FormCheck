"""Run one uploaded video through the provisional analysis pipeline."""

from __future__ import annotations

import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from formcheck.storage import ObjectStorage
from formcheck.worker.adapters import ObjectStorageArtifacts, StageProgress


def _ensure_analysis_path() -> None:
    root = Path(__file__).resolve().parents[3]
    for relative in (
        Path("packages") / "video",
        Path("packages") / "pose",
        Path("packages") / "biomechanics",
        Path("packages") / "rules",
        Path("services") / "worker" / "analysis",
    ):
        candidate = root / relative
        text = str(candidate)
        if candidate.is_dir() and text not in sys.path:
            sys.path.insert(0, text)


class _CallbackCancellation:
    def __init__(self, cancelled: Callable[[], bool]) -> None:
        self._cancelled = cancelled

    def raise_if_cancelled(self, analysis_id: UUID) -> None:
        from formcheck_analysis.ports import CancellationError

        if self._cancelled():
            raise CancellationError(analysis_id)


def run_pipeline(
    *,
    analysis_id: str,
    object_key: str,
    handedness: str,
    view_hint: str,
    pipeline_version: str,
    on_progress: Callable[[str, str | None, float | None], None],
    is_cancelled: Callable[[], bool],
    storage: ObjectStorage | None = None,
    model_path: Path | None = None,
):
    _ensure_analysis_path()
    from formcheck_analysis.pipeline import AnalysisFailure, AnalysisJobDraft, AnalysisPipeline
    from formcheck_analysis.stages import build_real_stages
    from formcheck_biomechanics.models import Handedness, ViewHint
    from formcheck_pose.assets import resolve_pose_model_path

    model = model_path or resolve_pose_model_path()
    if model is None:
        raise AnalysisFailure("Install FFmpeg and set MEDIAPIPE_POSE_MODEL_PATH before analyzing a video.")
    store = storage or ObjectStorage()
    with tempfile.TemporaryDirectory(prefix="formcheck-analysis-") as directory:
        work = Path(directory)
        artifacts = ObjectStorageArtifacts(store, work)
        stages = build_real_stages(
            work / "normalized",
            model,
            Handedness(handedness),
            ViewHint(view_hint),
            writer=artifacts,
            normalized_key=f"analyses/{analysis_id}/normalized/video.mp4",
        )
        pipeline = AnalysisPipeline(
            artifacts,
            artifacts,
            _CallbackCancellation(is_cancelled),
            StageProgress(on_progress),
            stages,
        )
        return pipeline.run(
            AnalysisJobDraft(
                analysis_id=UUID(analysis_id),
                video_object_key=object_key,
                handedness=Handedness(handedness),
                view_hint=ViewHint(view_hint),
                pipeline_version=pipeline_version,
            ),
            development_diagnostics=False,
        )
