from formcheck_video.eligibility import MAX_BYTES, assess_eligibility
from formcheck_video.models import VideoInspection


def _inspection(**overrides: object) -> VideoInspection:
    payload: dict[str, object] = {
        "source_sha256": "a" * 64,
        "duration_seconds": 10.0,
        "byte_size": 1024,
        "container": "mp4",
        "codec": "h264",
        "width": 1280,
        "height": 720,
        "nominal_fps": 30.0,
        "average_fps": 30.0,
        "rotation_degrees": 0,
        "stream_count": 1,
        "decode_ok": True,
        "source_pts_ms": (0, 33),
    }
    payload.update(overrides)
    return VideoInspection.model_validate(payload)


def test_inclusive_size_duration_and_fps_limits_stay_eligible() -> None:
    result = assess_eligibility(
        _inspection(byte_size=MAX_BYTES, duration_seconds=30.0, average_fps=120.0, nominal_fps=120.0)
    )

    assert result.eligible is True
    assert result.codes == []


def test_only_mp4_and_mov_containers_are_accepted() -> None:
    result = assess_eligibility(_inspection(container="avi"))

    assert result.eligible is False
    assert result.codes == ["VIDEO_UNSUPPORTED_CONTAINER"]


def test_over_limit_size_duration_and_fps_are_ineligible() -> None:
    too_big = assess_eligibility(_inspection(byte_size=MAX_BYTES + 1))
    too_long = assess_eligibility(_inspection(duration_seconds=30.01))
    slow = assess_eligibility(_inspection(average_fps=29.9, nominal_fps=29.9))

    assert too_big.codes == ["VIDEO_TOO_LARGE"]
    assert too_long.codes == ["VIDEO_TOO_LONG"]
    assert slow.codes == ["VIDEO_FPS_UNSUPPORTED"]
    assert too_big.eligible is False


def test_decode_failure_uses_stable_code() -> None:
    result = assess_eligibility(_inspection(decode_ok=False))

    assert result.codes == ["VIDEO_DECODE_FAILED"]
    assert result.remediation


def test_below_720p_warns_and_remains_eligible() -> None:
    result = assess_eligibility(_inspection(width=640, height=480))

    assert result.eligible is True
    assert result.warnings == ["VIDEO_LOW_RESOLUTION"]
