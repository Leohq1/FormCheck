from pathlib import Path
from uuid import UUID

import pytest
from formcheck_analysis.pipeline import AnalysisJobDraft, AnalysisPipeline, PipelineStages
from formcheck_analysis.ports import AnalysisStage, CancellationError
from formcheck_analysis.testing_ports import (
    ExplicitCancellation,
    InMemoryProgress,
    LocalArtifactStore,
)
from formcheck_biomechanics.models import (
    Handedness,
    QualityDisposition,
    QualityReport,
    StrokeWindow,
    ViewHint,
)
from formcheck_rules.models import CalibrationStatus, CandidateRuleEvaluation, DiagnosticOutcome

ANALYSIS_ID = UUID("11111111-1111-4111-8111-111111111111")


class _CancelAfterMaterialize:
    def __init__(self) -> None:
        self.calls = 0

    def raise_if_cancelled(self, analysis_id: UUID) -> None:
        self.calls += 1
        if self.calls >= 2:
            raise CancellationError(analysis_id)


def _job() -> AnalysisJobDraft:
    return AnalysisJobDraft(
        analysis_id=ANALYSIS_ID,
        video_object_key="analyses/demo/source/clip.mp4",
        handedness=Handedness.RIGHT,
        view_hint=ViewHint.REAR_THREE_QUARTER,
    )


def _quality(*, eligible: bool) -> QualityReport:
    return QualityReport(
        overall=0.8 if eligible else None,
        eligible=eligible,
        disposition=QualityDisposition.ELIGIBLE if eligible else QualityDisposition.INELIGIBLE,
        warnings=[] if eligible else ["body_not_fully_visible"],
        remediation=[] if eligible else ["Keep the full body in frame."],
    )


def _stages(calls: list[str], *, eligible: bool = True) -> PipelineStages:
    def inspect(path: Path) -> object:
        calls.append("inspect")
        return path

    def normalize(path: Path) -> object:
        calls.append("normalize")
        return path

    def pose(path: Path) -> object:
        calls.append("pose")
        return path

    def quality(pose_result: object, view: ViewHint) -> QualityReport:
        del pose_result, view
        calls.append("quality")
        return _quality(eligible=eligible)

    def segment(pose_result: object) -> StrokeWindow | None:
        del pose_result
        calls.append("segment")
        return StrokeWindow(start_ms=0, end_ms=400, confidence=0.7)

    def phases(pose_result: object, window: StrokeWindow) -> object:
        del pose_result, window
        calls.append("phases")
        return None

    def features(pose_result: object, window: StrokeWindow | None, view: ViewHint) -> tuple:
        del pose_result, window, view
        calls.append("features")
        return ()

    def rules(features_result: tuple, diagnostics_enabled: bool) -> tuple[CandidateRuleEvaluation, ...]:
        del features_result
        calls.append(f"rules:{diagnostics_enabled}")
        if not diagnostics_enabled:
            return ()
        return (
            CandidateRuleEvaluation(
                rule_id="clear.low_arm_extension.v1",
                enabled=False,
                calibration_status=CalibrationStatus.NOT_CALIBRATED,
                evaluation=DiagnosticOutcome.WOULD_TRIGGER,
                message="Candidate evaluation only; not a validated technique finding.",
            ),
        )

    return PipelineStages(inspect, normalize, pose, quality, segment, phases, features, rules)  # type: ignore[arg-type]


def _pipeline(tmp_path: Path, stages: PipelineStages, cancellation: object | None = None) -> AnalysisPipeline:
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"bytes")
    store = LocalArtifactStore(tmp_path / "objects")
    store.add_source("analyses/demo/source/clip.mp4", source)
    return AnalysisPipeline(
        store,
        store,
        cancellation or ExplicitCancellation(),  # type: ignore[arg-type]
        InMemoryProgress(),
        stages,
    )


def test_stage_order_and_diagnostic_modes(tmp_path: Path) -> None:
    calls: list[str] = []
    progress = InMemoryProgress()
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"bytes")
    store = LocalArtifactStore(tmp_path / "objects")
    store.add_source("analyses/demo/source/clip.mp4", source)
    pipeline = AnalysisPipeline(store, store, ExplicitCancellation(), progress, _stages(calls))

    developed = pipeline.run(_job(), development_diagnostics=True)
    produced = pipeline.run(_job(), development_diagnostics=False)

    assert calls[:8] == ["inspect", "normalize", "pose", "quality", "segment", "phases", "features", "rules:True"]
    assert developed.diagnostics is not None
    assert developed.diagnostics.candidate_rule_evaluations[0].evaluation is DiagnosticOutcome.WOULD_TRIGGER
    assert developed.findings == []
    assert "diagnostics" not in produced.to_production_dict()
    assert produced.findings == []
    assert [event.stage for event in progress.events if event.message_key == "preprocessing_completed"]


def test_ineligible_quality_stops_downstream_faults(tmp_path: Path) -> None:
    calls: list[str] = []
    result = _pipeline(tmp_path, _stages(calls, eligible=False)).run(_job())

    assert "segment" not in calls
    assert "rules:True" not in calls and "rules:False" not in calls
    assert result.findings == []
    assert result.quality.eligible is False


def test_cancellation_after_materialize_skips_normalization(tmp_path: Path) -> None:
    calls: list[str] = []
    progress = InMemoryProgress()
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"bytes")
    store = LocalArtifactStore(tmp_path / "objects")
    store.add_source("analyses/demo/source/clip.mp4", source)
    pipeline = AnalysisPipeline(store, store, _CancelAfterMaterialize(), progress, _stages(calls))

    with pytest.raises(CancellationError):
        pipeline.run(_job())

    assert calls == []
    assert AnalysisStage.NORMALIZE not in [event.stage for event in progress.events]
    assert "preprocessing_completed" not in [event.message_key for event in progress.events]
