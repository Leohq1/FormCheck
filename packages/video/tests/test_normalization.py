from pathlib import Path

import pytest
from formcheck_video.errors import VideoTechnicalError
from formcheck_video.models import VideoInspection
from formcheck_video.normalization import build_normalization_command, normalize_video
from formcheck_video.process import ProcessResult


def _inspection(**overrides: object) -> VideoInspection:
    payload: dict[str, object] = {
        "source_sha256": "b" * 64,
        "duration_seconds": 1.0,
        "byte_size": 10,
        "container": "mp4",
        "codec": "h264",
        "width": 3840,
        "height": 2160,
        "nominal_fps": 60.0,
        "average_fps": 60.0,
        "rotation_degrees": 90,
        "stream_count": 2,
        "decode_ok": True,
        "source_pts_ms": (0, 16, 33),
    }
    payload.update(overrides)
    return VideoInspection.model_validate(payload)


def test_command_uses_sixty_fps_h264_and_no_shell_string() -> None:
    command = build_normalization_command(
        Path("in.mp4"),
        Path("out.mp4"),
        source_fps=60,
        width=3840,
        height=2160,
        rotation_degrees=90,
    )

    assert isinstance(command, list)
    assert all(isinstance(part, str) for part in command)
    assert command[0] == "ffmpeg"
    assert "60" in command[command.index("-vf") + 1]
    assert "libx264" in command
    assert "yuv420p" in command
    assert "-an" in command
    assert "0:v:0" in command
    assert "transpose=1" in command[command.index("-vf") + 1]
    assert "rotate=0" in command
    assert "setpts=PTS-STARTPTS" in command[command.index("-vf") + 1]
    assert "scale=1080:1920" in command[command.index("-vf") + 1]
    assert not any("|" in part or "&&" in part for part in command)


def test_slower_source_uses_thirty_fps_and_caps_the_long_edge() -> None:
    command = build_normalization_command(
        Path("in.mp4"),
        Path("out.mp4"),
        source_fps=30,
        width=1280,
        height=720,
        rotation_degrees=0,
    )
    filters = command[command.index("-vf") + 1]

    assert "fps=30" in filters
    assert "scale=1280:720" in filters
    assert "transpose" not in filters


class _WritingRunner:
    def run(self, args: list[str], *, timeout_seconds: float) -> ProcessResult:
        del timeout_seconds
        Path(args[-1]).write_bytes(b"normalized")
        return ProcessResult(tuple(args), 0, "", "")


class _FailingRunner:
    def run(self, args: list[str], *, timeout_seconds: float) -> ProcessResult:
        del timeout_seconds
        return ProcessResult(tuple(args), 1, "", "boom")


def test_successful_normalization_replaces_outputs_atomically(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    video_output = tmp_path / "video.mp4"
    timestamps = tmp_path / "timestamps.json"

    result = normalize_video(
        source,
        video_output,
        timestamps,
        runner=_WritingRunner(),
        inspection=_inspection(width=1280, height=720, rotation_degrees=0, average_fps=30, nominal_fps=30),
    )

    assert video_output.read_bytes() == b"normalized"
    assert "normalization.v1" in timestamps.read_text(encoding="utf-8")
    assert result.output_fps == 30
    assert not list(tmp_path.glob("*.partial"))


def test_failed_normalization_keeps_preexisting_output(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    video_output = tmp_path / "video.mp4"
    video_output.write_bytes(b"keep")
    timestamps = tmp_path / "timestamps.json"
    timestamps.write_text("keep", encoding="utf-8")

    with pytest.raises(VideoTechnicalError) as caught:
        normalize_video(
            source,
            video_output,
            timestamps,
            runner=_FailingRunner(),
            inspection=_inspection(),
        )

    assert "source" not in caught.value.safe_message
    assert video_output.read_bytes() == b"keep"
    assert timestamps.read_text(encoding="utf-8") == "keep"
