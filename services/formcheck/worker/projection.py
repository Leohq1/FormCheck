"""Map a provisional pipeline result onto the public analysis-result schema."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from formcheck.worker.fixtures import failed_result


PROVISIONAL_LOW_ARM_CUTOFF_DEG = 140.0
PROVISIONAL_LOW_ARM_MIN_CONFIDENCE = 0.5
LOW_ARM_FEATURE = "dominant_elbow_angle_at_max_wrist_height_deg"


def public_result_from_pipeline(
    produced: dict[str, Any],
    *,
    analysis_id: str,
    expires_at: datetime,
    correlation_id: str,
    pipeline_version: str,
) -> tuple[dict[str, Any], str]:
    quality = produced.get("quality") or {}
    eligible = bool(quality.get("eligible"))
    warnings = [str(item) for item in quality.get("warnings") or []]
    remediation = [str(item) for item in quality.get("remediation") or []]
    overall = quality.get("overall")
    if not isinstance(overall, (int, float)) or isinstance(overall, bool):
        overall = 0.0
    versions = produced.get("versions") or {}
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    status = "completed" if eligible else "inconclusive"
    findings = list(produced.get("findings") or [])
    if eligible and not findings:
        findings = _provisional_low_arm_findings(produced.get("features"))
    payload: dict[str, Any] = {
        "schema_version": "1",
        "analysis_id": analysis_id,
        "status": status,
        "quality": {"overall": float(overall), "warnings": warnings},
        "stroke": _stroke(produced.get("stroke"), produced.get("phases")),
        "findings": findings,
        "feedback": _feedback(eligible, bool(findings)),
        "versions": {
            "pipeline": pipeline_version,
            "pose_estimator": str(versions.get("pose_estimator") or "mediapipe-pose-landmarker"),
            "feature_schema": str(versions.get("feature_schema") or "1"),
            "rule_set": str(versions.get("rule_set") or "clear.low_arm_extension.v1"),
            "corpus": "none",
            "embedding": "none",
            "generation": "none",
            "result_schema": "1",
        },
        "error": None
        if eligible
        else {
            "code": "POSE_QUALITY_INELIGIBLE",
            "safe_message": remediation[0] if remediation else "This recording could not be analyzed reliably.",
            "retryable": False,
            "remediation": remediation,
            "correlation_id": correlation_id,
        },
        "completed_at": now,
        "expires_at": expires_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return payload, status


def assets_missing_result(
    analysis_id: str,
    expires_at: datetime,
    correlation_id: str,
    *,
    pipeline_version: str,
) -> dict[str, Any]:
    payload = failed_result(
        analysis_id,
        expires_at,
        correlation_id,
        pipeline_version=pipeline_version,
    )
    payload["error"] = {
        "code": "ANALYSIS_ASSETS_MISSING",
        "safe_message": "The analysis worker is missing FFmpeg or the pose model.",
        "retryable": False,
        "remediation": ["Install FFmpeg and provide the MediaPipe pose model on the worker."],
        "correlation_id": correlation_id,
    }
    return payload


def pipeline_failed_result(
    analysis_id: str,
    expires_at: datetime,
    correlation_id: str,
    *,
    pipeline_version: str,
    safe_message: str,
) -> dict[str, Any]:
    payload = failed_result(
        analysis_id,
        expires_at,
        correlation_id,
        pipeline_version=pipeline_version,
    )
    payload["error"]["safe_message"] = safe_message
    payload["error"]["code"] = "ANALYSIS_PIPELINE_ERROR"
    return payload


def _stroke(window: object, phases: object) -> dict[str, Any]:
    if not isinstance(window, dict):
        return {
            "type": "overhead_clear",
            "start_time_ms": None,
            "end_time_ms": None,
            "contact_time_ms": None,
            "confidence": None,
        }
    stroke = window.get("stroke") or window.get("type") or "overhead_clear"
    return {
        "type": stroke,
        "start_time_ms": window.get("start_ms", window.get("start_time_ms")),
        "end_time_ms": window.get("end_ms", window.get("end_time_ms")),
        "contact_time_ms": _contact_ms(phases),
        "confidence": window.get("confidence"),
    }


def _contact_ms(phases: object) -> int | None:
    if not isinstance(phases, dict):
        return None
    for phase in phases.get("phases") or []:
        if not isinstance(phase, dict):
            continue
        if phase.get("name") == "contact" and phase.get("available") and isinstance(phase.get("start_ms"), int):
            return phase["start_ms"]
    return None


def _provisional_low_arm_findings(features: object) -> list[dict[str, Any]]:
    """Test cutoff only. A measured angle below the provisional cutoff becomes a public finding."""
    if not isinstance(features, list):
        return []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("name") != LOW_ARM_FEATURE:
            continue
        value = feature.get("value")
        confidence = feature.get("confidence")
        if feature.get("available") is not True:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            continue
        if confidence < PROVISIONAL_LOW_ARM_MIN_CONFIDENCE or value >= PROVISIONAL_LOW_ARM_CUTOFF_DEG:
            continue
        return [
            {
                "rule_id": "clear.low_arm_extension.v1",
                "label": "Low arm extension at maximum reach",
                "severity": "moderate",
                "confidence": float(confidence),
                "evidence": [
                    {
                        "feature": LOW_ARM_FEATURE,
                        "value": float(value),
                        "unit": "deg",
                    }
                ],
                "retrieval_tags": ["overhead_clear", "arm_extension"],
            }
        ]
    return []


def _feedback(eligible: bool, has_finding: bool = False) -> dict[str, Any]:
    if has_finding:
        summary = "A provisional check found a low elbow angle at the top of the swing."
        limitations = [
            f"The {PROVISIONAL_LOW_ARM_CUTOFF_DEG:.0f} degree cutoff is a provisional test and is not calibrated."
        ]
    elif eligible:
        summary = "No supported fault was detected."
        limitations = ["Technique rules are not calibrated, so this result does not include a coaching fault."]
    else:
        summary = ""
        limitations = ["Technique findings are withheld when pose quality is insufficient."]
    return {
        "summary": summary,
        "tips": [],
        "limitations": limitations,
        "model": "none",
        "prompt_version": "1",
    }
