from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from formcheck_video.errors import VideoTechnicalError
from formcheck_video.models import NormalizationResult, VideoInspection
from formcheck_video.process import ProcessRunner
from formcheck_video.timestamps import map_output_to_source

CONTRACT_VERSION = "normalization.v1"
MAX_EDGE = 1920


def target_fps(source_fps: float) -> int:
    return 60 if source_fps >= 50 else 30


def even_capped_size(width: int, height: int, *, rotation_degrees: int = 0) -> tuple[int, int]:
    rotated_width, rotated_height = (height, width) if abs(rotation_degrees) % 180 == 90 else (width, height)
    long_edge = max(rotated_width, rotated_height)
    scale = 1.0 if long_edge <= MAX_EDGE else MAX_EDGE / long_edge
    return _even(rotated_width * scale), _even(rotated_height * scale)


def build_normalization_command(
    source: Path,
    output: Path,
    *,
    source_fps: float,
    width: int,
    height: int,
    rotation_degrees: int,
) -> list[str]:
    fps = target_fps(source_fps)
    out_width, out_height = even_capped_size(width, height, rotation_degrees=rotation_degrees)
    filters = [
        *_rotation_filters(rotation_degrees),
        f"fps={fps}",
        f"scale={out_width}:{out_height}",
        "setpts=PTS-STARTPTS",
    ]
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        ",".join(filters),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-metadata:s:v",
        "rotate=0",
        str(output),
    ]


def normalize_video(
    source: Path,
    video_output: Path,
    timestamp_output: Path,
    *,
    runner: ProcessRunner,
    inspection: VideoInspection,
    timeout_seconds: float = 120.0,
    ffmpeg_version: str = "unknown",
) -> NormalizationResult:
    video_output.parent.mkdir(parents=True, exist_ok=True)
    timestamp_output.parent.mkdir(parents=True, exist_ok=True)
    temp_video = video_output.with_name(video_output.name + ".partial")
    temp_timestamps = timestamp_output.with_name(timestamp_output.name + ".partial")
    fps_value = inspection.average_fps if inspection.average_fps is not None else inspection.nominal_fps
    if fps_value is None:
        raise VideoTechnicalError("The video frame rate could not be read.")
    command = build_normalization_command(
        source,
        temp_video,
        source_fps=fps_value,
        width=inspection.width,
        height=inspection.height,
        rotation_degrees=inspection.rotation_degrees,
    )
    try:
        result = runner.run(command, timeout_seconds=timeout_seconds)
        if result.returncode != 0 or not temp_video.is_file():
            raise VideoTechnicalError("Video normalization failed.")
        output_fps = target_fps(fps_value)
        output_width, output_height = even_capped_size(
            inspection.width,
            inspection.height,
            rotation_degrees=inspection.rotation_degrees,
        )
        duration_ms = int(round(inspection.duration_seconds * 1000))
        frame_count = max(1, int(round(inspection.duration_seconds * output_fps)))
        output_timestamps = tuple(min(duration_ms, int(round(index * 1000 / output_fps))) for index in range(frame_count))
        mapped = map_output_to_source(output_timestamps, inspection.source_pts_ms or (0,))
        payload = {
            "contract_version": CONTRACT_VERSION,
            "frames": [entry.model_dump() for entry in mapped],
        }
        temp_timestamps.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(temp_video, video_output)
        os.replace(temp_timestamps, timestamp_output)
    except VideoTechnicalError:
        _discard(temp_video, temp_timestamps)
        raise
    except Exception as exc:
        _discard(temp_video, temp_timestamps)
        raise VideoTechnicalError("Video normalization failed.") from exc
    return NormalizationResult(
        video_sha256=_sha256(video_output),
        timestamp_sha256=_sha256(timestamp_output),
        output_width=output_width,
        output_height=output_height,
        output_fps=output_fps,
        ffmpeg_version=ffmpeg_version,
        contract_version=CONTRACT_VERSION,
        command=tuple(command),
        timestamps=mapped,
    )


def _rotation_filters(rotation_degrees: int) -> list[str]:
    turns = abs(rotation_degrees) % 360
    if turns == 90:
        return ["transpose=1"]
    if turns == 180:
        return ["hflip", "vflip"]
    if turns == 270:
        return ["transpose=2"]
    return []


def _even(value: float) -> int:
    even = int(round(value)) // 2 * 2
    return max(2, even)


def _discard(*paths: Path) -> None:
    for path in paths:
        if path.is_file():
            path.unlink()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()
