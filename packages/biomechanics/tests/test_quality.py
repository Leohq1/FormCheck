from formcheck_biomechanics.config import QualityContext
from formcheck_biomechanics.models import Handedness, ViewHint
from formcheck_biomechanics.quality import assess_pose_quality
from formcheck_pose.models import (
    CANONICAL_LANDMARKS,
    LandmarkName,
    PoseFrame,
    PoseLandmark,
    PoseSequence,
)


def _sequence(
    present: set[LandmarkName] | None = None,
    *,
    visibility: float = 0.9,
    detected: int = 1,
    timestamps: tuple[int, ...] = (0,),
) -> PoseSequence:
    required = present if present is not None else set(CANONICAL_LANDMARKS)
    frames = []
    for index, timestamp in enumerate(timestamps):
        landmarks = []
        for name in CANONICAL_LANDMARKS:
            if name in required:
                landmarks.append(
                    PoseLandmark(name=name, available=True, x=0.2, y=0.2, visibility=visibility, presence=visibility)
                )
            else:
                landmarks.append(PoseLandmark(name=name, available=False, missing_reason="not_detected"))
        frames.append(
            PoseFrame(index=index, timestamp_ms=timestamp, detected_pose_count=detected, landmarks=tuple(landmarks))
        )
    return PoseSequence(estimator_name="test", estimator_version="0", model_version="0", frames=tuple(frames))


def _context(**overrides: object) -> QualityContext:
    payload = {
        "view_hint": ViewHint.SIDE,
        "sharpness": 100.0,
        "camera_motion": 0.2,
        "low_resolution": False,
        "ends_before_follow_through": False,
    }
    payload.update(overrides)
    return QualityContext(**payload)  # type: ignore[arg-type]


def test_adequate_input_is_eligible() -> None:
    report = assess_pose_quality(_sequence(), _context(), Handedness.RIGHT)

    assert report.eligible is True
    assert report.overall == 1.0
    assert report.version == "quality.v1-provisional"


def test_cropped_body_is_ineligible_without_a_fabricated_score() -> None:
    present = set(CANONICAL_LANDMARKS) - {LandmarkName.LEFT_ANKLE, LandmarkName.RIGHT_ANKLE}
    report = assess_pose_quality(_sequence(present), _context(), Handedness.RIGHT)

    assert report.eligible is False
    assert report.overall is None
    assert "body_not_fully_visible" in report.warnings
    assert report.remediation


def test_unreliable_dominant_arm_and_long_occlusion_fail() -> None:
    report = assess_pose_quality(
        _sequence(visibility=0.1, timestamps=(0, 100, 400)),
        _context(),
        Handedness.RIGHT,
    )

    assert report.eligible is False
    assert "dominant_arm_unreliable" in report.warnings


def test_low_resolution_warns_without_failing_an_otherwise_good_clip() -> None:
    report = assess_pose_quality(_sequence(), _context(low_resolution=True), Handedness.RIGHT)

    assert report.eligible is True
    assert "low_resolution" in report.warnings


def test_unsupported_view_second_person_blur_and_early_ending() -> None:
    unsupported = assess_pose_quality(_sequence(), _context(view_hint=None), Handedness.RIGHT)
    crowded = assess_pose_quality(_sequence(detected=2), _context(), Handedness.RIGHT)
    blurry = assess_pose_quality(_sequence(), _context(sharpness=1.0, camera_motion=20.0), Handedness.RIGHT)
    short = assess_pose_quality(_sequence(), _context(ends_before_follow_through=True), Handedness.RIGHT)

    assert "unsupported_view" in unsupported.warnings and unsupported.overall is None
    assert "multiple_person_interference" in crowded.warnings
    assert "motion_blur" in blurry.warnings and "camera_motion" in blurry.warnings
    assert "clip_ends_before_follow_through" in short.warnings
    assert all(item.eligible is False for item in (unsupported, crowded, blurry, short))
