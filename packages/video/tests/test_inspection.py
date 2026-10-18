import json
import subprocess
from pathlib import Path

import pytest
from formcheck_video.errors import VideoTechnicalError
from formcheck_video.inspection import inspect_video
from formcheck_video.models import parse_ffprobe_fraction
from formcheck_video.process import ProcessResult, SubprocessRunner


class ScriptedRunner:
    def __init__(self, responses: list[ProcessResult]) -> None:
        self.responses = list(responses)
        self.calls: list[list[str]] = []
        self.timeouts: list[float] = []

    def run(self, args: list[str], *, timeout_seconds: float) -> ProcessResult:
        self.calls.append(list(args))
        self.timeouts.append(timeout_seconds)
        if not self.responses:
            raise AssertionError("unexpected video tool call")
        return self.responses.pop(0)


def _probe_payload() -> str:
    return json.dumps(
        {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "avg_frame_rate": "30000/1001",
                    "r_frame_rate": "30/1",
                    "side_data_list": [{"rotation": -90}],
                },
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "1.5", "size": "40"},
        }
    )


def _frames_payload() -> str:
    return json.dumps(
        {
            "frames": [
                {"best_effort_timestamp_time": "0.000"},
                {"pts_time": "0.033"},
            ]
        }
    )


def test_ffprobe_fraction_parses_exactly() -> None:
    assert parse_ffprobe_fraction("30000/1001") == __import__("fractions").Fraction(30000, 1001)
    assert parse_ffprobe_fraction("0/0") is None


def test_subprocess_runner_uses_argument_list_shell_false_and_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args, 0, b"{}", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = SubprocessRunner().run(["ffprobe", "clip.mp4"], timeout_seconds=4.5)

    assert result.returncode == 0
    assert captured["args"] == ["ffprobe", "clip.mp4"]
    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["shell"] is False
    assert kwargs["timeout"] == 4.5


def test_inspection_records_rotation_pts_and_exact_frame_rate(tmp_path: Path) -> None:
    source = tmp_path / "clear.mp4"
    source.write_bytes(b"source-bytes")
    runner = ScriptedRunner(
        [
            ProcessResult(("ffprobe",), 0, _probe_payload(), ""),
            ProcessResult(("ffprobe",), 0, _frames_payload(), ""),
        ]
    )

    inspection = inspect_video(source, runner=runner, timeout_seconds=9)

    assert all(isinstance(call, list) for call in runner.calls)
    assert runner.timeouts == [9, 9]
    assert inspection.rotation_degrees == -90
    assert inspection.source_pts_ms == (0, 33)
    assert inspection.average_fps == pytest.approx(float(__import__("fractions").Fraction(30000, 1001)))
    assert inspection.stream_count == 2
    assert inspection.container == "mp4"
    assert inspection.byte_size == len(b"source-bytes")
    assert len(inspection.source_sha256) == 64


def test_malformed_probe_raises_without_source_path(tmp_path: Path) -> None:
    source = tmp_path / "private-athlete.mp4"
    source.write_bytes(b"x")
    runner = ScriptedRunner([ProcessResult(("ffprobe",), 0, "not-json", "")])

    with pytest.raises(VideoTechnicalError) as caught:
        inspect_video(source, runner=runner)

    message = caught.value.safe_message
    assert "private-athlete" not in message
    assert str(tmp_path) not in message
