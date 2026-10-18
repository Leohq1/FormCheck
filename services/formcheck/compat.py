"""Temporary wire-format shim for the pre-sign-off frontend (Person 1).

Canonical storage and default API responses use ratified Milestone A shapes.
When FORMCHECK_INTERIM_RESULT_SHIM=1 (default), GET /result projects to the
interim apps/web types so local demos keep working until Person 1 remaps.
"""

from __future__ import annotations

from typing import Any

_SEVERITY = {"minor": "low", "moderate": "medium", "major": "high"}


def _quality_label(overall: float) -> str:
    if overall >= 0.7:
        return "acceptable"
    if overall >= 0.4:
        return "borderline"
    return "poor"


def to_interim_result(ratified: dict[str, Any]) -> dict[str, Any]:
    """Project a ratified AnalysisResult dict to the interim frontend shape."""
    stroke = ratified.get("stroke") or {}
    quality = ratified.get("quality") or {}
    feedback = ratified.get("feedback") or {}
    error = ratified.get("error")

    findings = []
    for finding in ratified.get("findings") or []:
        evidence_items = finding.get("evidence") or []
        if evidence_items:
            evidence = "; ".join(
                f"{e.get('feature')}={e.get('value')}{e.get('unit')}" for e in evidence_items
            )
        else:
            evidence = ""
        findings.append(
            {
                "rule_id": finding.get("rule_id"),
                "label": finding.get("label"),
                "severity": _SEVERITY.get(finding.get("severity", ""), finding.get("severity")),
                "confidence": finding.get("confidence"),
                "evidence": evidence,
            }
        )

    recommendations = []
    citations = []
    for tip in feedback.get("tips") or []:
        cite_ids: list[str] = []
        for cite in tip.get("citations") or []:
            cite_id = f"{cite.get('source_id')}:{cite.get('chunk_id')}"
            cite_ids.append(cite_id)
            citations.append(
                {
                    "id": cite_id,
                    "title": cite.get("source_id") or cite_id,
                    "locator": cite.get("locator") or "",
                }
            )
        recommendations.append(
            {
                "title": tip.get("title"),
                "body": tip.get("explanation"),
                "exercise": tip.get("practice_cue"),
                "citation_ids": cite_ids,
            }
        )

    interim_error = None
    if error:
        remediation = error.get("remediation") or []
        interim_error = {
            "code": error.get("code"),
            "message": error.get("safe_message"),
            "retry_may_work": error.get("retryable"),
            "recording_remediation": "; ".join(remediation) if remediation else None,
            "correlation_id": error.get("correlation_id"),
        }

    versions = dict(ratified.get("versions") or {})
    # Interim frontend expected older version keys; keep ratified keys and aliases.
    if "pose_estimator" in versions and "pose" not in versions:
        versions["pose"] = versions["pose_estimator"]
    if "feature_schema" in versions and "feature" not in versions:
        versions["feature"] = versions["feature_schema"]
    if "rule_set" in versions and "rule" not in versions:
        versions["rule"] = versions["rule_set"]

    status = ratified.get("status")
    inconclusive_reason = None
    retake_guidance: list[str] = []
    if status == "inconclusive" and error:
        inconclusive_reason = error.get("safe_message")
        retake_guidance = list(error.get("remediation") or [])

    overall = quality.get("overall")
    if isinstance(overall, (int, float)):
        quality_overall: Any = _quality_label(float(overall))
        notes = list(quality.get("warnings") or [])
    else:
        quality_overall = overall
        notes = list(quality.get("notes") or quality.get("warnings") or [])

    return {
        "schema_version": "1.0.0",
        "analysis_id": ratified.get("analysis_id"),
        "status": status,
        "stroke": stroke.get("type") if isinstance(stroke, dict) else stroke,
        "quality": {"overall": quality_overall, "notes": notes},
        "stroke_confidence": stroke.get("confidence") if isinstance(stroke, dict) else None,
        "phase_confidence": None,
        "findings": findings,
        "recommendations": recommendations,
        "citations": citations,
        "limitations": list(feedback.get("limitations") or []),
        "inconclusive_reason": inconclusive_reason,
        "retake_guidance": retake_guidance,
        "error": interim_error,
        "completed_at": ratified.get("completed_at"),
        "expires_at": ratified.get("expires_at"),
        "versions": versions,
    }
