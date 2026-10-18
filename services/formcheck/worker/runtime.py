"""Choose a scripted fixture outcome or the real video pipeline."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from formcheck.worker.projection import (
    assets_missing_result,
    pipeline_failed_result,
    public_result_from_pipeline,
)


class AnalysisCancelled(Exception):
    pass


def missing_assets() -> list[str]:
    missing: list[str] = []
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    if shutil.which("ffprobe") is None:
        missing.append("ffprobe")
    raw = os.environ.get("MEDIAPIPE_POSE_MODEL_PATH", "").strip()
    if not raw or not Path(raw).is_file():
        missing.append("pose model")
    return missing


def execute_video_analysis(
    *,
    analysis_id: str,
    expires_at: datetime,
    correlation_id: str,
    pipeline_version: str,
    missing_tools: list[str] | None = None,
    runner: Callable[[], Any] | None = None,
) -> tuple[dict[str, Any], str]:
    missing = missing_assets() if missing_tools is None else missing_tools
    if missing:
        return (
            assets_missing_result(
                analysis_id,
                expires_at,
                correlation_id,
                pipeline_version=pipeline_version,
            ),
            "failed",
        )
    try:
        if runner is None:
            raise RuntimeError("A video runner is required.")
        produced = runner()
    except AnalysisCancelled:
        raise
    except Exception as exc:
        if exc.__class__.__name__ == "CancellationError":
            raise AnalysisCancelled from exc
        return (
            pipeline_failed_result(
                analysis_id,
                expires_at,
                correlation_id,
                pipeline_version=pipeline_version,
                safe_message=_safe_message(exc),
            ),
            "failed",
        )
    if hasattr(produced, "to_production_dict"):
        produced = produced.to_production_dict()
    return public_result_from_pipeline(
        produced,
        analysis_id=analysis_id,
        expires_at=expires_at,
        correlation_id=correlation_id,
        pipeline_version=pipeline_version,
    )


def _safe_message(exc: BaseException) -> str:
    message = getattr(exc, "safe_message", None)
    if isinstance(message, str) and message and "\\" not in message and "/" not in message:
        return message
    return "Something went wrong while analyzing this video. You can try again."
