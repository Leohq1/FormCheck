from __future__ import annotations

import hashlib
import json
from pathlib import Path

from formcheck_video.errors import VideoTechnicalError
from formcheck_video.models import VideoInspection, parse_ffprobe_fraction
from formcheck_video.process import ProcessResult, ProcessRunner, SubprocessRunner

_ACCEPTED_CONTAINERS = ("mp4", "mov", "quicktime")


def inspect_video(
    path: Path,
    *,
    runner: ProcessRunner | None = None,
    timeout_seconds: float = 30.0,
) -> VideoInspection:
    tool = runner or SubprocessRunner()
    source = Path(path)
    digest = _sha256(source)
    metadata = _probe_json(
        tool,
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(source),
        ],
        timeout_seconds=timeout_seconds,
    )
    frames = _probe_json(
        tool,
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "frame=best_effort_timestamp_time,pts_time",
            "-of",
            "json",
            str(source),
        ],
        timeout_seconds=timeout_seconds,
    )
    return _inspection_from_probe(source, digest, metadata, frames)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _probe_json(runner: ProcessRunner, args: list[str], *, timeout_seconds: float) -> dict[str, object]:
    try:
        result = runner.run(args, timeout_seconds=timeout_seconds)
    except VideoTechnicalError:
        raise
    except Exception as exc:
        raise VideoTechnicalError("The video could not be inspected.") from exc
    return _parse_probe(result)


def _parse_probe(result: ProcessResult) -> dict[str, object]:
    if result.returncode != 0:
        raise VideoTechnicalError("The video could not be inspected.")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise VideoTechnicalError("The video inspector returned malformed output.") from exc
    if not isinstance(payload, dict):
        raise VideoTechnicalError("The video inspector returned malformed output.")
    return payload


def _inspection_from_probe(
    source: Path,
    digest: str,
    metadata: dict[str, object],
    frames: dict[str, object],
) -> VideoInspection:
    streams = metadata.get("streams")
    fmt = metadata.get("format")
    stream_list = streams if isinstance(streams, list) else []
    format_info = fmt if isinstance(fmt, dict) else {}
    video = next((item for item in stream_list if isinstance(item, dict) and item.get("codec_type") == "video"), None)
    container = _container(str(format_info.get("format_name", "")))
    duration = _float_or_zero(format_info.get("duration"))
    width = int(video.get("width", 0)) if isinstance(video, dict) else 0
    height = int(video.get("height", 0)) if isinstance(video, dict) else 0
    nominal = _ratio_float(video.get("r_frame_rate")) if isinstance(video, dict) else None
    average = _ratio_float(video.get("avg_frame_rate")) if isinstance(video, dict) else None
    rotation = _rotation(video) if isinstance(video, dict) else 0
    codec = str(video.get("codec_name")) if isinstance(video, dict) and video.get("codec_name") else None
    pts = _presentation_timestamps(frames)
    return VideoInspection(
        source_sha256=digest,
        duration_seconds=duration,
        byte_size=source.stat().st_size,
        container=container,
        codec=codec,
        width=width,
        height=height,
        nominal_fps=nominal,
        average_fps=average,
        rotation_degrees=rotation,
        stream_count=len(stream_list),
        decode_ok=video is not None and bool(pts or video),
        source_pts_ms=pts,
    )


def _container(format_name: str) -> str:
    tokens = [part.strip() for part in format_name.split(",") if part.strip()]
    for accepted in _ACCEPTED_CONTAINERS:
        if accepted in tokens:
            return "mov" if accepted == "quicktime" else accepted
    return tokens[0] if tokens else "unknown"


def _ratio_float(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    fraction = parse_ffprobe_fraction(value)
    if fraction is None:
        return None
    return float(fraction)


def _float_or_zero(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _rotation(video: dict[str, object]) -> int:
    tags = video.get("tags")
    if isinstance(tags, dict) and tags.get("rotate") is not None:
        return int(float(str(tags["rotate"])))
    side_data = video.get("side_data_list")
    if isinstance(side_data, list):
        for item in side_data:
            if isinstance(item, dict) and item.get("rotation") is not None:
                return int(float(str(item["rotation"])))
    return 0


def _presentation_timestamps(frames: dict[str, object]) -> tuple[int, ...]:
    raw = frames.get("frames")
    if not isinstance(raw, list):
        return ()
    stamps: list[int] = []
    for frame in raw:
        if not isinstance(frame, dict):
            continue
        text = frame.get("best_effort_timestamp_time", frame.get("pts_time"))
        if text is None:
            continue
        stamps.append(int(round(float(str(text)) * 1000)))
    return tuple(stamps)
