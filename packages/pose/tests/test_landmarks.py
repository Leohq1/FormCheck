from formcheck_pose.landmarks import MEDIAPIPE_INDEX, BackendLandmark, map_landmarks
from formcheck_pose.models import CANONICAL_LANDMARKS, LandmarkName


def test_mapping_keeps_canonical_order_visibility_and_missing_reasons() -> None:
    raw: list[BackendLandmark | None] = [None] * len(CANONICAL_LANDMARKS)
    raw[MEDIAPIPE_INDEX[LandmarkName.RIGHT_WRIST]] = BackendLandmark(0.2, 0.3, -0.1, 0.77, 0.66)

    landmarks = map_landmarks(raw, missing_reason="not_detected")

    assert [item.name for item in landmarks] == list(CANONICAL_LANDMARKS)
    wrist = landmarks[MEDIAPIPE_INDEX[LandmarkName.RIGHT_WRIST]]
    assert wrist.available is True
    assert wrist.visibility == 0.77
    assert wrist.presence == 0.66
    assert wrist.relative_z == -0.1
    nose = landmarks[MEDIAPIPE_INDEX[LandmarkName.NOSE]]
    assert nose.available is False
    assert nose.missing_reason == "not_detected"
    assert nose.x is None
