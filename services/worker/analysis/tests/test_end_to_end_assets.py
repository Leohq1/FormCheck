import os
import shutil
from pathlib import Path

import pytest


@pytest.mark.assets
@pytest.mark.integration
def test_asset_backed_run_keeps_public_findings_empty(tmp_path: Path) -> None:
    missing: list[str] = []
    sample = os.environ.get("FORMCHECK_SAMPLE_VIDEO")
    model = os.environ.get("MEDIAPIPE_POSE_MODEL_PATH")
    if not sample or not Path(sample).is_file():
        missing.append("FORMCHECK_SAMPLE_VIDEO")
    if not model or not Path(model).is_file():
        missing.append("MEDIAPIPE_POSE_MODEL_PATH")
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    if shutil.which("ffprobe") is None:
        missing.append("ffprobe")
    if missing:
        pytest.skip("missing requirements: " + ", ".join(missing))

    from uuid import UUID

    from formcheck_analysis.pipeline import AnalysisJobDraft, AnalysisPipeline
    from formcheck_analysis.testing_ports import (
        ExplicitCancellation,
        InMemoryProgress,
        LocalArtifactStore,
    )
    from formcheck_biomechanics.models import Handedness, ViewHint

    source = Path(sample or "")
    store = LocalArtifactStore(tmp_path)
    key = "analyses/demo/source/overhead_clear.mp4"
    store.add_source(key, source)
    pipeline = AnalysisPipeline(
        store,
        store,
        ExplicitCancellation(),
        InMemoryProgress(),
        _real_stages(tmp_path, Path(model or "")),
    )
    findings = pipeline.run(
        AnalysisJobDraft(
            analysis_id=UUID("11111111-1111-4111-8111-111111111111"),
            video_object_key=key,
            handedness=Handedness.RIGHT,
            view_hint=ViewHint.SIDE,
        ),
        development_diagnostics=True,
    )
    produced = findings.to_production_dict()

    assert produced["schema_version"] == "0-draft"
    assert produced["findings"] == []
    assert "diagnostics" not in produced
    assert findings.diagnostics is not None
    for item in findings.diagnostics.candidate_rule_evaluations:
        assert item.enabled is False
        assert item.calibration_status.value == "not_calibrated"


def _real_stages(tmp_path: Path, model: Path):
    from formcheck_analysis.stages import build_real_stages
    from formcheck_biomechanics.models import Handedness, ViewHint

    return build_real_stages(tmp_path, model, Handedness.RIGHT, ViewHint.SIDE)
