from __future__ import annotations

from formcheck_pose.models import LandmarkName, PoseSequence

from formcheck_biomechanics.config import DOMINANT_ARM, QualityConfig, QualityContext
from formcheck_biomechanics.models import (
    Handedness,
    QualityComponent,
    QualityDisposition,
    QualityReport,
    ViewHint,
)


def assess_pose_quality(
    sequence: PoseSequence,
    context: QualityContext,
    handedness: Handedness,
    config: QualityConfig | None = None,
) -> QualityReport:
    settings = config or QualityConfig()
    shoulder, elbow, wrist = DOMINANT_ARM[handedness]
    components: list[QualityComponent] = []
    warnings: list[str] = []
    remediation: list[str] = []

    coverage = _coverage(sequence)
    components.append(QualityComponent(name="full_body", passed=coverage >= settings.minimum_coverage, detail=f"{coverage:.2f}"))
    if coverage < settings.minimum_coverage:
        warnings.append("body_not_fully_visible")
        remediation.append("Keep the full body in frame for the whole stroke.")

    arm_ok, occlusion_ms = _arm_status(sequence, (shoulder, elbow, wrist), settings)
    components.append(QualityComponent(name="dominant_arm", passed=arm_ok, detail=f"occlusion_ms={occlusion_ms}"))
    if not arm_ok:
        warnings.append("dominant_arm_unreliable")
        remediation.append("Keep the hitting arm visible and unobstructed.")

    interference = any(frame.detected_pose_count > 1 for frame in sequence.frames)
    components.append(QualityComponent(name="single_player", passed=not interference))
    if interference:
        warnings.append("multiple_person_interference")
        remediation.append("Record one player in the frame.")

    view_ok = context.view_hint in {ViewHint.SIDE, ViewHint.REAR_THREE_QUARTER}
    components.append(QualityComponent(name="view", passed=view_ok))
    if not view_ok:
        warnings.append("unsupported_view")
        remediation.append("Use a side or rear three-quarter camera view.")

    if context.low_resolution:
        warnings.append("low_resolution")
        remediation.append("720p or higher is recommended.")
        components.append(QualityComponent(name="resolution", passed=True, detail="warning"))
    else:
        components.append(QualityComponent(name="resolution", passed=True))

    blur_ok = context.sharpness is None or context.sharpness >= settings.minimum_sharpness
    motion_ok = context.camera_motion is None or context.camera_motion <= settings.maximum_camera_motion
    components.append(QualityComponent(name="sharpness", passed=blur_ok))
    components.append(QualityComponent(name="camera_motion", passed=motion_ok))
    if context.sharpness is not None and not blur_ok:
        warnings.append("motion_blur")
        remediation.append("Use a faster shutter or brighter court so the player is sharp.")
    if context.camera_motion is not None and not motion_ok:
        warnings.append("camera_motion")
        remediation.append("Keep the camera steady.")

    follow_ok = not context.ends_before_follow_through
    components.append(QualityComponent(name="follow_through", passed=follow_ok))
    if not follow_ok:
        warnings.append("clip_ends_before_follow_through")
        remediation.append("Keep recording through the follow-through.")

    blocking = [item for item in components if item.name not in {"resolution"} and not item.passed]
    eligible = not blocking
    if eligible:
        scores = [1.0 if item.passed else 0.0 for item in components if item.name != "resolution"]
        overall = min(scores) if scores else None
        disposition = QualityDisposition.ELIGIBLE
    else:
        overall = None
        disposition = QualityDisposition.INELIGIBLE
    return QualityReport(
        overall=overall,
        eligible=eligible,
        disposition=disposition,
        warnings=warnings,
        remediation=remediation,
        components=components,
        version=settings.version,
    )


def _coverage(sequence: PoseSequence) -> float:
    if not sequence.frames:
        return 0.0
    required = (
        LandmarkName.NOSE,
        LandmarkName.LEFT_HIP,
        LandmarkName.RIGHT_HIP,
        LandmarkName.LEFT_ANKLE,
        LandmarkName.RIGHT_ANKLE,
    )
    covered = 0
    for frame in sequence.frames:
        by_name = {item.name: item for item in frame.landmarks}
        if all(by_name[name].available and (by_name[name].visibility or 0) >= 0.5 for name in required):
            covered += 1
    return covered / len(sequence.frames)


def _arm_status(
    sequence: PoseSequence,
    names: tuple[LandmarkName, LandmarkName, LandmarkName],
    config: QualityConfig,
) -> tuple[bool, int]:
    longest = 0
    current = 0
    current_start: int | None = None
    previous: int | None = None
    reliable_frames = 0
    for frame in sequence.frames:
        by_name = {item.name: item for item in frame.landmarks}
        reliable = all(_reliable(by_name[name], config.minimum_visibility) for name in names)
        if reliable:
            reliable_frames += 1
            current = 0
            current_start = None
        else:
            if current_start is None:
                current_start = frame.timestamp_ms
            if previous is not None and current_start is not None:
                current = frame.timestamp_ms - current_start
            longest = max(longest, current)
        previous = frame.timestamp_ms
    if not sequence.frames:
        return False, 0
    fraction = reliable_frames / len(sequence.frames)
    return fraction >= config.minimum_coverage and longest <= config.maximum_occlusion_ms, longest


def _reliable(landmark: object, minimum_visibility: float) -> bool:
    available = bool(getattr(landmark, "available", False))
    visibility = getattr(landmark, "visibility", None)
    return available and visibility is not None and float(visibility) >= minimum_visibility
