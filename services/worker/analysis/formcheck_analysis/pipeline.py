"""PROVISIONAL: requires Person 2 approval before this composition is a production worker."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from formcheck_biomechanics.models import (
    FeatureValue,
    Handedness,
    PhaseSet,
    QualityReport,
    StrokeWindow,
    ViewHint,
)
from formcheck_rules.models import CandidateRuleEvaluation
from pydantic import BaseModel, ConfigDict

from formcheck_analysis.models import AnalysisDiagnostics, AnalysisFindings, VersionInfo
from formcheck_analysis.ports import (
    AnalysisStage,
    ArtifactReader,
    ArtifactWriter,
    CancellationPort,
    ProgressPort,
)


class AnalysisJobDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0-draft"
    analysis_id: UUID
    video_object_key: str
    stroke: str = "overhead_clear"
    handedness: Handedness
    view_hint: ViewHint
    pipeline_version: str = "2026.10.0"


class AnalysisFailure(Exception):
    def __init__(self, safe_message: str) -> None:
        super().__init__(safe_message)
        self.safe_message = safe_message


@dataclass
class PipelineStages:
    inspect: Callable[[Path], object]
    normalize: Callable[[Path], object]
    pose: Callable[[Path], object]
    quality: Callable[[object, ViewHint], QualityReport]
    segment: Callable[[object], StrokeWindow | None]
    phases: Callable[[object, StrokeWindow], PhaseSet | None]
    features: Callable[[object, StrokeWindow | None, ViewHint], tuple[FeatureValue, ...]]
    rules: Callable[[tuple[FeatureValue, ...], bool], tuple[CandidateRuleEvaluation, ...]]


class AnalysisPipeline:
    """PROVISIONAL: requires Person 2 approval."""

    def __init__(
        self,
        reader: ArtifactReader,
        writer: ArtifactWriter,
        cancellation: CancellationPort,
        progress: ProgressPort,
        stages: PipelineStages,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.cancellation = cancellation
        self.progress = progress
        self.stages = stages

    def run(self, job: AnalysisJobDraft, *, development_diagnostics: bool = False) -> AnalysisFindings:
        self._check(job.analysis_id)
        source = self.reader.materialize(job.video_object_key)
        self._report(job, AnalysisStage.MATERIALIZE, "source_materialized")
        self._check(job.analysis_id)
        inspection = self.stages.inspect(source)
        self._report(job, AnalysisStage.INSPECT, "video_inspected")
        self._check(job.analysis_id)
        self.stages.normalize(source)
        self._report(job, AnalysisStage.NORMALIZE, "preprocessing_completed")
        self._check(job.analysis_id)
        self._report(job, AnalysisStage.POSE, "pose_started")
        pose = self.stages.pose(source)
        self._report(job, AnalysisStage.POSE, "pose_estimated")
        quality = self.stages.quality(pose, job.view_hint)
        self._report(job, AnalysisStage.QUALITY, "quality_assessed")
        stroke: StrokeWindow | None = None
        phases: PhaseSet | None = None
        features: tuple[FeatureValue, ...] = ()
        diagnostics: tuple[CandidateRuleEvaluation, ...] = ()
        if quality.eligible:
            self._check(job.analysis_id)
            stroke = self.stages.segment(pose)
            self._report(job, AnalysisStage.SEGMENT, "stroke_segmented")
            if stroke is not None:
                phases = self.stages.phases(pose, stroke)
                self._report(job, AnalysisStage.PHASES, "phases_estimated")
            features = self.stages.features(pose, stroke, job.view_hint)
            self._report(job, AnalysisStage.FEATURES, "features_extracted")
            diagnostics = self.stages.rules(features, development_diagnostics)
            self._report(job, AnalysisStage.RULES, "rules_evaluated")
        self._report(job, AnalysisStage.ASSEMBLE, "result_assembled")
        del inspection
        return AnalysisFindings(
            analysis_id=str(job.analysis_id),
            quality=quality,
            stroke=stroke,
            phases=phases,
            features=list(features),
            findings=[],
            versions=VersionInfo(
                pipeline=job.pipeline_version,
                pose_estimator="mediapipe-pose-landmarker",
                feature_schema="1",
                rule_set="clear.low_arm_extension.v1",
            ),
            diagnostics=AnalysisDiagnostics(candidate_rule_evaluations=list(diagnostics))
            if development_diagnostics
            else None,
            handedness=job.handedness,
            view_hint=job.view_hint,
        )

    def _check(self, analysis_id: UUID) -> None:
        self.cancellation.raise_if_cancelled(analysis_id)

    def _report(self, job: AnalysisJobDraft, stage: AnalysisStage, message_key: str) -> None:
        if "/" in message_key or "\\" in message_key:
            raise AnalysisFailure("Progress could not be reported.")
        self.progress.report(job.analysis_id, stage, None, message_key)


def analyze_joint_samples(
    samples: list[object],
    *,
    analysis_id: str,
    diagnostics_enabled: bool = False,
) -> dict[str, object]:
    """Score supplied joint samples. This does not run video or pose estimation."""
    from formcheck_biomechanics.features.arm_extension import (
        JointSample,
        dominant_elbow_angle_at_max_wrist_height,
    )
    from formcheck_rules.engine import evaluate_clear_arm_extension
    from formcheck_rules.engine import production_findings as sample_findings

    typed = [sample if isinstance(sample, JointSample) else sample for sample in samples]
    feature = dominant_elbow_angle_at_max_wrist_height(typed)  # type: ignore[arg-type]
    evaluation = evaluate_clear_arm_extension(feature, diagnostics_enabled=diagnostics_enabled)
    payload: dict[str, object] = {
        "schema_version": "0-draft",
        "analysis_id": analysis_id,
        "quality": {"overall": 1.0 if feature.available else 0.0, "warnings": []},
        "stroke": {"type": "overhead_clear", "confidence": feature.confidence},
        "features": [
            {
                "name": feature.name,
                "value": feature.value,
                "unit": feature.unit,
                "confidence": feature.confidence,
                "available": feature.available,
                "feature_version": feature.version,
                "reason": feature.reason,
            }
        ],
        "findings": list(sample_findings(evaluation)),
        "versions": {
            "pose_estimator": "not-run",
            "feature_schema": feature.version,
            "rule_set": "clear.low_arm_extension.v1:disabled",
        },
    }
    if diagnostics_enabled:
        payload["diagnostics"] = [
            {
                "rule_id": item.rule_id,
                "evaluation": item.evaluation,
                "feature": item.feature,
                "value": item.value,
                "threshold_deg": item.threshold_deg,
                "threshold_label": item.threshold_label,
            }
            for item in evaluation.diagnostics
        ]
    return payload
