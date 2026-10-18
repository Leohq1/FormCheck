"""Compose a pose window into production findings. Diagnostics stay out of that payload."""

from __future__ import annotations

from formcheck_biomechanics.features.arm_extension import (
    JointSample,
    dominant_elbow_angle_at_max_wrist_height,
)
from formcheck_rules.engine import evaluate_clear_arm_extension, production_findings


def analyze_joint_samples(
    samples: list[JointSample],
    *,
    analysis_id: str,
    diagnostics_enabled: bool = False,
) -> dict[str, object]:
    feature = dominant_elbow_angle_at_max_wrist_height(samples)
    evaluation = evaluate_clear_arm_extension(feature, diagnostics_enabled=diagnostics_enabled)
    payload: dict[str, object] = {
        "schema_version": "0-draft",
        "analysis_id": analysis_id,
        "quality": {"overall": 1.0 if feature.available else 0.0, "warnings": []},
        "stroke": {"type": "overhead_clear", "confidence": feature.confidence},
        "features": [
            {
                "name": feature.name,
                "value": feature.value,
                "unit": feature.unit,
                "confidence": feature.confidence,
                "available": feature.available,
                "feature_version": feature.version,
                "reason": feature.reason,
            }
        ],
        "findings": list(production_findings(evaluation)),
        "versions": {
            "pose_estimator": "not-run",
            "feature_schema": feature.version,
            "rule_set": "clear.low_arm_extension.v1:disabled",
        },
    }
    if diagnostics_enabled:
        payload["diagnostics"] = [
            {
                "rule_id": item.rule_id,
                "evaluation": item.evaluation,
                "feature": item.feature,
                "value": item.value,
                "threshold_deg": item.threshold_deg,
                "threshold_label": item.threshold_label,
            }
            for item in evaluation.diagnostics
        ]
    return payload
