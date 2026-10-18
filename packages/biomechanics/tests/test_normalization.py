from formcheck_biomechanics.config import NormalizationConfig
from formcheck_biomechanics.models import Handedness
from formcheck_biomechanics.normalization import normalize_pose
from formcheck_pose.models import (
    CANONICAL_LANDMARKS,
    LandmarkName,
    PoseFrame,
    PoseLandmark,
    PoseSequence,
)


def _sequence(points: dict[LandmarkName, tuple[float, float]]) -> PoseSequence:
    landmarks = []
    for name in CANONICAL_LANDMARKS:
        if name in points:
            x, y = points[name]
            landmarks.append(PoseLandmark(name=name, available=True, x=x, y=y, visibility=1, presence=1))
        else:
            landmarks.append(PoseLandmark(name=name, available=False, missing_reason="not_detected"))
    frame = PoseFrame(index=0, timestamp_ms=0, detected_pose_count=1, landmarks=tuple(landmarks))
    return PoseSequence(estimator_name="test", estimator_version="0", model_version="0", frames=(frame,))


def _body(origin_x: float = 0.0, origin_y: float = 0.0, scale: float = 1.0) -> dict[LandmarkName, tuple[float, float]]:
    return {
        LandmarkName.LEFT_HIP: (origin_x - 10 * scale, origin_y),
        LandmarkName.RIGHT_HIP: (origin_x + 10 * scale, origin_y),
        LandmarkName.LEFT_SHOULDER: (origin_x - 10 * scale, origin_y - 40 * scale),
        LandmarkName.RIGHT_SHOULDER: (origin_x + 10 * scale, origin_y - 40 * scale),
        LandmarkName.RIGHT_WRIST: (origin_x + 20 * scale, origin_y - 20 * scale),
    }


def test_pelvis_centering_and_torso_scale() -> None:
    normalized = normalize_pose(_sequence(_body()), Handedness.RIGHT, NormalizationConfig())
    frame = normalized.frames[0]

    assert frame.scale_source == "torso_length"
    assert frame.scale == 40
    wrist = frame.landmark(LandmarkName.RIGHT_WRIST)
    assert wrist.x is not None and wrist.y is not None
    assert wrist.x == 0.5
    assert wrist.y == 0.5
    assert wrist.visibility == 1


def test_translation_and_uniform_scale_do_not_change_body_coordinates() -> None:
    original = normalize_pose(_sequence(_body()), Handedness.RIGHT)
    moved = normalize_pose(_sequence(_body(100, -30, 2)), Handedness.RIGHT)
    left = original.frames[0].landmark(LandmarkName.RIGHT_WRIST)
    right = moved.frames[0].landmark(LandmarkName.RIGHT_WRIST)

    assert left.x == right.x
    assert left.y == right.y


def test_missing_scale_makes_coordinates_unavailable() -> None:
    points = {
        LandmarkName.LEFT_HIP: (0.0, 0.0),
        LandmarkName.RIGHT_HIP: (0.0, 0.0),
        LandmarkName.RIGHT_WRIST: (1.0, 1.0),
    }
    normalized = normalize_pose(_sequence(points), Handedness.RIGHT)
    wrist = normalized.frames[0].landmark(LandmarkName.RIGHT_WRIST)

    assert normalized.frames[0].scale is None
    assert wrist.available is False
    assert wrist.x is None


def test_left_handed_clip_matches_its_right_handed_mirror() -> None:
    right = normalize_pose(_sequence(_body()), Handedness.RIGHT).frames[0].landmark(LandmarkName.RIGHT_WRIST)
    mirrored = _body()
    pelvis_x = 0.0
    swapped = {}
    for name, (x, y) in mirrored.items():
        reflected = (2 * pelvis_x - x, y)
        partner = {
            LandmarkName.LEFT_HIP: LandmarkName.RIGHT_HIP,
            LandmarkName.RIGHT_HIP: LandmarkName.LEFT_HIP,
            LandmarkName.LEFT_SHOULDER: LandmarkName.RIGHT_SHOULDER,
            LandmarkName.RIGHT_SHOULDER: LandmarkName.LEFT_SHOULDER,
            LandmarkName.RIGHT_WRIST: LandmarkName.LEFT_WRIST,
        }[name]
        swapped[partner] = reflected
    left = normalize_pose(_sequence(swapped), Handedness.LEFT).frames[0].landmark(LandmarkName.RIGHT_WRIST)

    assert left.x == right.x
    assert left.y == right.y
