"""Compose the provisional video, pose, feature, and disabled-rule stages."""

from __future__ import annotations

from pathlib import Path

from formcheck_biomechanics.config import QualityContext
from formcheck_biomechanics.features.base import FeatureContext
from formcheck_biomechanics.features.registry import build_default_registry
from formcheck_biomechanics.models import FeatureValue, Handedness, PhaseSet, StrokeWindow, ViewHint
from formcheck_biomechanics.normalization import normalize_pose
from formcheck_biomechanics.phases import detect_phases
from formcheck_biomechanics.quality import assess_pose_quality
from formcheck_biomechanics.segmentation import segment_overhead_clear
from formcheck_biomechanics.signals import compute_motion_signals
from formcheck_rules.catalog import PRODUCTION_CATALOG
from formcheck_rules.engine import RuleContext, RuleEngine
from formcheck_rules.models import CandidateRuleEvaluation
from formcheck_video.eligibility import assess_eligibility
from formcheck_video.errors import VideoTechnicalError
from formcheck_video.inspection import inspect_video
from formcheck_video.models import NormalizationResult, VideoInspection
from formcheck_video.normalization import normalize_video

from formcheck_analysis.pipeline import AnalysisFailure, PipelineStages
from formcheck_analysis.ports import ArtifactWriter


class _VideoRun:
    def __init__(
        self,
        work_dir: Path,
        model_path: Path,
        handedness: Handedness,
        view: ViewHint,
        writer: ArtifactWriter | None,
        normalized_key: str | None,
    ) -> None:
        self.work_dir = work_dir
        self.model_path = model_path
        self.handedness = handedness
        self.view = view
        self.writer = writer
        self.normalized_key = normalized_key
        self.inspection: VideoInspection | None = None
        self.normalization: NormalizationResult | None = None
        self.normalized_video: Path | None = None
        self.low_resolution = False

    def inspect(self, path: Path) -> VideoInspection:
        try:
            inspection = inspect_video(path)
        except VideoTechnicalError as exc:
            raise AnalysisFailure(exc.safe_message) from exc
        eligibility = assess_eligibility(inspection)
        self.inspection = inspection
        self.low_resolution = "VIDEO_LOW_RESOLUTION" in eligibility.warnings
        if not eligibility.eligible:
            message = eligibility.remediation[0] if eligibility.remediation else "This video cannot be analyzed."
            raise AnalysisFailure(message)
        return inspection

    def normalize(self, path: Path) -> NormalizationResult:
        if self.inspection is None:
            raise AnalysisFailure("The video was not inspected.")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        video_output = self.work_dir / "normalized.mp4"
        timestamp_output = self.work_dir / "timestamps.json"
        try:
            result = normalize_video(
                path,
                video_output,
                timestamp_output,
                runner=_subprocess_runner(),
                inspection=self.inspection,
            )
        except VideoTechnicalError as exc:
            raise AnalysisFailure(exc.safe_message) from exc
        self.normalization = result
        self.normalized_video = video_output
        if self.writer is not None and self.normalized_key:
            self.writer.put_file(self.normalized_key, video_output, content_type="video/mp4")
        return result

    def pose(self, path: Path) -> object:
        del path
        if self.normalized_video is None or self.normalization is None:
            raise AnalysisFailure("Video normalization did not produce a file.")
        from formcheck_pose.mediapipe_estimator import MediaPipePoseEstimator, PoseEstimationError

        stamps = _strict_timestamps(self.normalization)
        try:
            return MediaPipePoseEstimator(self.model_path).infer(self.normalized_video, stamps)
        except PoseEstimationError as exc:
            raise AnalysisFailure(exc.safe_message) from exc

    def quality(self, pose: object, view: ViewHint) -> object:
        signals = None
        if self.normalized_video is not None:
            from formcheck_video.frame_quality import FrameQualityConfig, measure_frame_quality

            signals = measure_frame_quality(self.normalized_video, FrameQualityConfig())
        context = QualityContext(
            view_hint=view,
            sharpness=signals.sharpness if signals is not None and signals.available else None,
            camera_motion=signals.camera_motion if signals is not None and signals.available else None,
            low_resolution=self.low_resolution,
        )
        return assess_pose_quality(pose, context, self.handedness)  # type: ignore[arg-type]

    def segment(self, pose: object) -> StrokeWindow | None:
        normalized = normalize_pose(pose, self.handedness)  # type: ignore[arg-type]
        return segment_overhead_clear(compute_motion_signals(normalized)).window

    def phases(self, pose: object, window: StrokeWindow) -> PhaseSet:
        normalized = normalize_pose(pose, self.handedness)  # type: ignore[arg-type]
        signals = compute_motion_signals(normalized)
        return detect_phases(normalized, window, signals).phases

    def features(self, pose: object, window: StrokeWindow | None, view: ViewHint) -> tuple[FeatureValue, ...]:
        normalized = normalize_pose(pose, self.handedness)  # type: ignore[arg-type]
        return build_default_registry().extract_all(
            FeatureContext(sequence=normalized, window=window or _full_clip_window(normalized), view=view)
        )

    def rules(
        self,
        features: tuple[FeatureValue, ...],
        diagnostics_enabled: bool,
    ) -> tuple[CandidateRuleEvaluation, ...]:
        result = RuleEngine(PRODUCTION_CATALOG).evaluate(
            features,
            RuleContext(view=self.view),
            diagnostics_enabled=diagnostics_enabled,
        )
        return result.diagnostics


def build_real_stages(
    work_dir: Path,
    model_path: Path,
    handedness: Handedness,
    view: ViewHint,
    *,
    writer: ArtifactWriter | None = None,
    normalized_key: str | None = None,
) -> PipelineStages:
    run = _VideoRun(work_dir, model_path, handedness, view, writer, normalized_key)
    return PipelineStages(
        run.inspect,
        run.normalize,
        run.pose,
        run.quality,  # type: ignore[arg-type]
        run.segment,
        run.phases,
        run.features,
        run.rules,
    )


def _subprocess_runner():
    from formcheck_video.process import SubprocessRunner

    return SubprocessRunner()


def _full_clip_window(sequence: object) -> StrokeWindow | None:
    frames = getattr(sequence, "frames", ())
    if not frames:
        return None
    return StrokeWindow(start_ms=frames[0].timestamp_ms, end_ms=frames[-1].timestamp_ms, confidence=0.0)


def _strict_timestamps(result: NormalizationResult) -> list[int]:
    stamps: list[int] = []
    last = -1
    for entry in result.timestamps:
        stamp = entry.normalized_timestamp_ms
        if stamp <= last:
            stamp = last + 1
        stamps.append(stamp)
        last = stamp
    if not stamps:
        raise AnalysisFailure("The normalized video has no timestamps.")
    return stamps
