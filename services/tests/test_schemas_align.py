"""Smoke tests that do not require Docker services."""

from formcheck.compat import to_interim_result
from formcheck.contract_validate import (
    validate_analysis_job,
    validate_analysis_progress,
    validate_analysis_result,
)
from formcheck.schemas import AnalysisJob, AnalysisProgressEvent, AnalysisResult, CreateAnalysisRequest
from formcheck.worker.fixtures import (
    completed_result,
    failed_result,
    hours_from_now,
    inconclusive_result,
)


def test_create_request_accepts_frontend_fields():
    body = CreateAnalysisRequest(
        stroke="overhead_clear",
        handedness="right",
        view_hint="side",
        consent=True,
        filename="clear.mp4",
        content_type="video/mp4",
        byte_size=1024,
    )
    assert body.byte_size == 1024
    assert body.consent is True


def test_completed_fixture_matches_result_schema():
    payload = completed_result("11111111-1111-4111-8111-111111111111", hours_from_now(24))
    validate_analysis_result(payload)
    result = AnalysisResult.model_validate(payload)
    assert result.status == "completed"
    assert result.findings[0].severity in {"minor", "moderate", "major"}
    assert isinstance(result.findings[0].evidence, list)
    assert result.feedback.tips
    assert result.error is None


def test_inconclusive_fixture_requires_error():
    payload = inconclusive_result(
        "11111111-1111-4111-8111-111111111112",
        hours_from_now(24),
        correlation_id="corr-test",
    )
    validate_analysis_result(payload)
    assert payload["error"]["code"] == "POSE_BODY_CROPPED"


def test_failed_fixture_matches_result_schema():
    payload = failed_result(
        "11111111-1111-4111-8111-111111111113",
        hours_from_now(24),
        "corr-test",
    )
    validate_analysis_result(payload)


def test_analysis_job_schema():
    job = AnalysisJob(
        schema_version="1",
        analysis_id="11111111-1111-4111-8111-111111111111",
        video_object_key="analyses/11111111-1111-4111-8111-111111111111/source/clear.mp4",
        stroke="overhead_clear",
        handedness="right",
        view_hint="side",
        pipeline_version="2026.10.0",
    )
    validate_analysis_job(job.model_dump())


def test_progress_event_schema():
    event = AnalysisProgressEvent(
        schema_version="1",
        analysis_id="11111111-1111-4111-8111-111111111111",
        stage="pose_estimation",
        progress=None,
        message_key="estimating_pose",
        updated_at="2026-10-17T20:00:00Z",
    )
    validate_analysis_progress(event.model_dump())


def test_interim_shim_maps_severity_and_feedback():
    payload = completed_result("11111111-1111-4111-8111-111111111111", hours_from_now(24))
    interim = to_interim_result(payload)
    assert interim["findings"][0]["severity"] == "medium"
    assert isinstance(interim["findings"][0]["evidence"], str)
    assert interim["recommendations"]
    assert interim["error"] is None
