from datetime import datetime, timezone

from formcheck.contract_validate import validate_analysis_result
from formcheck.worker.projection import public_result_from_pipeline
from formcheck.worker.runtime import execute_video_analysis


def _expires() -> datetime:
    return datetime(2026, 10, 18, tzinfo=timezone.utc)


def test_eligible_pipeline_result_has_no_finding_and_validates() -> None:
    produced = {
        "quality": {"overall": 1.0, "eligible": True, "warnings": [], "remediation": []},
        "stroke": {"stroke": "overhead_clear", "start_ms": 100, "end_ms": 400, "confidence": 0.7},
        "phases": {
            "phases": [{"name": "contact", "start_ms": 250, "available": True}],
            "contact_available": True,
        },
        "findings": [],
        "versions": {
            "pose_estimator": "mediapipe-pose-landmarker",
            "feature_schema": "1",
            "rule_set": "clear.low_arm_extension.v1",
        },
    }

    result, status = public_result_from_pipeline(
        produced,
        analysis_id="11111111-1111-4111-8111-111111111111",
        expires_at=_expires(),
        correlation_id="corr-1",
        pipeline_version="2026.10.0",
    )

    assert status == "completed"
    assert result["findings"] == []
    assert result["stroke"]["contact_time_ms"] == 250
    assert result["error"] is None
    assert "low arm extension" not in result["feedback"]["summary"].lower()
    validate_analysis_result(result)


def test_angle_below_140_degrees_becomes_a_provisional_finding() -> None:
    produced = {
        "quality": {"overall": 1.0, "eligible": True, "warnings": [], "remediation": []},
        "stroke": {"stroke": "overhead_clear", "start_ms": 100, "end_ms": 400, "confidence": 0.7},
        "features": [
            {
                "name": "dominant_elbow_angle_at_max_wrist_height_deg",
                "value": 128.0,
                "unit": "deg",
                "confidence": 0.8,
                "available": True,
                "feature_version": "1",
            }
        ],
        "findings": [],
        "versions": {},
    }

    result, status = public_result_from_pipeline(
        produced,
        analysis_id="11111111-1111-4111-8111-111111111111",
        expires_at=_expires(),
        correlation_id="corr-1",
        pipeline_version="2026.10.0",
    )

    assert status == "completed"
    assert result["findings"][0]["rule_id"] == "clear.low_arm_extension.v1"
    assert result["findings"][0]["evidence"][0]["value"] == 128.0
    validate_analysis_result(result)


def test_angle_above_140_degrees_stays_empty() -> None:
    produced = {
        "quality": {"overall": 1.0, "eligible": True, "warnings": [], "remediation": []},
        "features": [
            {
                "name": "dominant_elbow_angle_at_max_wrist_height_deg",
                "value": 176.0,
                "unit": "deg",
                "confidence": 0.9,
                "available": True,
                "feature_version": "1",
            }
        ],
        "findings": [],
        "versions": {},
    }

    result, status = public_result_from_pipeline(
        produced,
        analysis_id="11111111-1111-4111-8111-111111111111",
        expires_at=_expires(),
        correlation_id="corr-1",
        pipeline_version="2026.10.0",
    )

    assert status == "completed"
    assert result["findings"] == []
    assert "low arm extension" not in result["feedback"]["summary"].lower()
    validate_analysis_result(result)


def test_angle_at_the_provisional_cutoff_stays_empty() -> None:
    produced = {
        "quality": {"overall": 1.0, "eligible": True, "warnings": [], "remediation": []},
        "features": [
            {
                "name": "dominant_elbow_angle_at_max_wrist_height_deg",
                "value": 140.0,
                "unit": "deg",
                "confidence": 0.9,
                "available": True,
                "feature_version": "1",
            }
        ],
        "findings": [],
        "versions": {},
    }

    result, _status = public_result_from_pipeline(
        produced,
        analysis_id="11111111-1111-4111-8111-111111111111",
        expires_at=_expires(),
        correlation_id="corr-1",
        pipeline_version="2026.10.0",
    )

    assert result["findings"] == []
    validate_analysis_result(result)


def test_ineligible_quality_is_inconclusive() -> None:
    produced = {
        "quality": {
            "overall": None,
            "eligible": False,
            "warnings": ["body_not_fully_visible"],
            "remediation": ["Keep the full body in frame for the whole stroke."],
        },
        "stroke": None,
        "findings": [],
        "versions": {},
    }

    result, status = public_result_from_pipeline(
        produced,
        analysis_id="11111111-1111-4111-8111-111111111111",
        expires_at=_expires(),
        correlation_id="corr-1",
        pipeline_version="2026.10.0",
    )

    assert status == "inconclusive"
    assert result["quality"]["overall"] == 0.0
    assert result["error"]["code"] == "POSE_QUALITY_INELIGIBLE"
    assert result["error"]["remediation"] == ["Keep the full body in frame for the whole stroke."]
    validate_analysis_result(result)


def test_missing_worker_tools_fail_without_calling_the_pipeline() -> None:
    def runner() -> dict:
        raise AssertionError("pipeline should not run")

    result, status = execute_video_analysis(
        analysis_id="11111111-1111-4111-8111-111111111111",
        expires_at=_expires(),
        correlation_id="corr-1",
        pipeline_version="2026.10.0",
        missing_tools=["ffmpeg", "pose model"],
        runner=runner,
    )

    assert status == "failed"
    assert result["error"]["code"] == "ANALYSIS_ASSETS_MISSING"
    assert result["findings"] == []
    validate_analysis_result(result)
