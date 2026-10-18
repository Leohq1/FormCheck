"""Sample AnalysisResult payloads matching packages/contracts examples."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _versions(pipeline_version: str = "2026.10.0") -> dict[str, str]:
    return {
        "pipeline": pipeline_version,
        "pose_estimator": "mediapipe-0.10",
        "feature_schema": "1",
        "rule_set": "1",
        "corpus": "1",
        "embedding": "text-embedding-3-small",
        "generation": "gpt-placeholder",
        "result_schema": "1",
    }


def completed_result(
    analysis_id: str,
    expires_at: datetime,
    *,
    pipeline_version: str = "2026.10.0",
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "schema_version": "1",
        "analysis_id": analysis_id,
        "status": "completed",
        "quality": {"overall": 0.84, "warnings": []},
        "stroke": {
            "type": "overhead_clear",
            "start_time_ms": 4200,
            "end_time_ms": 7100,
            "contact_time_ms": 6240,
            "confidence": 0.78,
        },
        "findings": [
            {
                "rule_id": "clear.low_arm_extension.v1",
                "label": "Low arm extension at maximum reach",
                "severity": "moderate",
                "confidence": 0.81,
                "evidence": [
                    {
                        "feature": "dominant_elbow_angle_at_max_wrist_height_deg",
                        "value": 128,
                        "unit": "deg",
                    }
                ],
                "retrieval_tags": [
                    "overhead_clear",
                    "contact_reach",
                    "arm_extension",
                ],
            }
        ],
        "feedback": {
            "summary": (
                "The clip suggests the striking arm was short of full extension "
                "near the highest wrist height."
            ),
            "tips": [
                {
                    "finding_id": "clear.low_arm_extension.v1",
                    "title": "Reach through contact",
                    "explanation": (
                        "Practice a longer arm line at the top of the swing so power "
                        "travels into the racket."
                    ),
                    "practice_cue": (
                        "Shadow-swing 10 overhead clears focusing on full arm "
                        "extension at the top."
                    ),
                    "citations": [
                        {
                            "source_id": "source-001",
                            "chunk_id": "chunk-014",
                            "locator": "Section 4.2",
                        }
                    ],
                }
            ],
            "limitations": [
                "Contact time was estimated from body motion because the racket "
                "and shuttle were not tracked."
            ],
            "model": "gpt-placeholder",
            "prompt_version": "1",
        },
        "versions": _versions(pipeline_version),
        "error": None,
        "completed_at": _iso(now),
        "expires_at": _iso(expires_at),
    }


def inconclusive_result(
    analysis_id: str,
    expires_at: datetime,
    *,
    correlation_id: str,
    pipeline_version: str = "2026.10.0",
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "schema_version": "1",
        "analysis_id": analysis_id,
        "status": "inconclusive",
        "quality": {
            "overall": 0.22,
            "warnings": ["Dominant ankles left the frame during the swing."],
        },
        "stroke": {
            "type": "overhead_clear",
            "start_time_ms": None,
            "end_time_ms": None,
            "contact_time_ms": None,
            "confidence": None,
        },
        "findings": [],
        "feedback": {
            "summary": "",
            "tips": [],
            "limitations": [
                "Technique findings are withheld when pose quality is insufficient."
            ],
            "model": "none",
            "prompt_version": "1",
        },
        "versions": {
            **_versions(pipeline_version),
            "embedding": "none",
            "generation": "none",
        },
        "error": {
            "code": "POSE_BODY_CROPPED",
            "safe_message": "The full body was not visible throughout the stroke.",
            "retryable": False,
            "remediation": [
                "Move the camera farther away.",
                "Keep both feet and the hitting arm in the frame.",
            ],
            "correlation_id": correlation_id,
        },
        "completed_at": _iso(now),
        "expires_at": _iso(expires_at),
    }


def failed_result(
    analysis_id: str,
    expires_at: datetime,
    correlation_id: str,
    *,
    pipeline_version: str = "2026.10.0",
) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "analysis_id": analysis_id,
        "status": "failed",
        "quality": {"overall": 0.0, "warnings": []},
        "stroke": {
            "type": "overhead_clear",
            "start_time_ms": None,
            "end_time_ms": None,
            "contact_time_ms": None,
            "confidence": None,
        },
        "findings": [],
        "feedback": {
            "summary": "",
            "tips": [],
            "limitations": [],
            "model": "none",
            "prompt_version": "1",
        },
        "versions": {
            **_versions(pipeline_version),
            "embedding": "none",
            "generation": "none",
        },
        "error": {
            "code": "ANALYSIS_PIPELINE_ERROR",
            "safe_message": (
                "Something went wrong while analyzing this video. You can try again."
            ),
            "retryable": True,
            "remediation": [],
            "correlation_id": correlation_id,
        },
        "completed_at": None,
        "expires_at": _iso(expires_at),
    }


def expired_result(
    analysis_id: str,
    expires_at: datetime,
    correlation_id: str,
    *,
    pipeline_version: str = "2026.10.0",
) -> dict[str, Any]:
    payload = completed_result(
        analysis_id, expires_at, pipeline_version=pipeline_version
    )
    payload["status"] = "expired"
    payload["error"] = {
        "code": "ANALYSIS_EXPIRED",
        "safe_message": "This analysis has expired and is no longer available.",
        "retryable": False,
        "remediation": ["Upload a new recording to start again."],
        "correlation_id": correlation_id,
    }
    return payload


def outcome_from_filename(filename: str) -> str:
    lower = filename.lower()
    for token in ("inconclusive", "failed", "expired"):
        if token in lower:
            return token
    return "completed"


def hours_from_now(hours: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)
