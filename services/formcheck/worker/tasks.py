"""Durable fake analysis worker (Person 2 orchestration)."""

from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import dramatiq
from jsonschema import ValidationError

from formcheck.config import get_settings
from formcheck.contract_validate import (
    format_validation_error,
    validate_analysis_job,
    validate_analysis_progress,
    validate_analysis_result,
)
from formcheck.db import SessionLocal
from formcheck.models import Analysis, DeletionOutbox
from formcheck.schemas import AnalysisJob, AnalysisProgressEvent
from formcheck.storage import ObjectStorage
from formcheck.worker import broker as _broker  # noqa: F401 — configures broker
from formcheck.worker.fixtures import (
    completed_result,
    expired_result,
    failed_result,
    inconclusive_result,
    outcome_from_filename,
)

logger = logging.getLogger(__name__)

PROCESSING_STAGES = [
    ("preprocessing", "normalizing_video"),
    ("pose_estimation", "estimating_pose"),
    ("phase_detection", "detecting_phases"),
    ("rule_evaluation", "evaluating_rules"),
    ("retrieval", "retrieving_coaching"),
    ("generating", "generating_feedback"),
]


def _is_cancelled(analysis: Analysis) -> bool:
    return analysis.status in {"cancelled", "deleted"} or analysis.deleted_at is not None


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _apply_progress(
    db: Any,
    analysis: Analysis,
    *,
    stage: str,
    message_key: str | None,
    progress: float | None,
) -> None:
    now = datetime.now(timezone.utc)
    event = AnalysisProgressEvent(
        schema_version="1",
        analysis_id=str(analysis.id),
        stage=stage,  # type: ignore[arg-type]
        progress=progress,
        message_key=message_key,
        updated_at=now.isoformat().replace("+00:00", "Z"),
    )
    payload = event.model_dump()
    validate_analysis_progress(payload)

    analysis.status = stage
    analysis.stage = stage
    analysis.message_key = message_key
    analysis.progress = progress
    analysis.updated_at = now
    db.commit()


def _persist_result(db: Any, analysis: Analysis, result: dict[str, Any], *, status: str) -> None:
    validate_analysis_result(result)
    analysis.status = status
    analysis.stage = status
    analysis.message_key = status
    analysis.result_json = result
    analysis.progress = 1.0
    analysis.updated_at = datetime.now(timezone.utc)
    if status in {"completed", "inconclusive"}:
        analysis.completed_at = datetime.now(timezone.utc)
    db.commit()


@dramatiq.actor(max_retries=2, time_limit=600_000)
def run_fake_analysis(job: dict[str, Any]) -> None:
    """Accept a full AnalysisJob payload (analysis-job.schema.json)."""
    settings = get_settings()
    stage_ms = max(50, settings.fake_worker_stage_ms) / 1000.0

    try:
        validate_analysis_job(job)
        parsed = AnalysisJob.model_validate(job)
    except (ValidationError, Exception) as exc:
        logger.error("Invalid AnalysisJob: %s", exc)
        return

    analysis_id = parsed.analysis_id
    db = SessionLocal()
    try:
        analysis = db.get(Analysis, uuid.UUID(analysis_id))
        if analysis is None:
            logger.warning("Analysis %s not found", analysis_id)
            return
        if _is_cancelled(analysis):
            return

        # Prefer job fields (source of truth for the worker) over stale row copies.
        if analysis.source_object_key != parsed.video_object_key:
            logger.warning(
                "Job video_object_key mismatch for %s: row=%s job=%s",
                analysis_id,
                analysis.source_object_key,
                parsed.video_object_key,
            )

        for stage, message_key in PROCESSING_STAGES:
            db.refresh(analysis)
            if _is_cancelled(analysis):
                return
            _apply_progress(
                db, analysis, stage=stage, message_key=message_key, progress=None
            )
            time.sleep(stage_ms)

        db.refresh(analysis)
        if _is_cancelled(analysis):
            return

        pipeline = parsed.pipeline_version or settings.pipeline_version
        outcome = outcome_from_filename(analysis.filename)
        if outcome == "expired":
            result = expired_result(
                str(analysis.id),
                analysis.expires_at,
                analysis.correlation_id,
                pipeline_version=pipeline,
            )
            _persist_result(db, analysis, result, status="expired")
        elif outcome == "inconclusive":
            result = inconclusive_result(
                str(analysis.id),
                analysis.expires_at,
                correlation_id=analysis.correlation_id,
                pipeline_version=pipeline,
            )
            _persist_result(db, analysis, result, status="inconclusive")
        elif outcome == "failed":
            result = failed_result(
                str(analysis.id),
                analysis.expires_at,
                analysis.correlation_id,
                pipeline_version=pipeline,
            )
            _persist_result(db, analysis, result, status="failed")
        else:
            result = completed_result(
                str(analysis.id),
                analysis.expires_at,
                pipeline_version=pipeline,
            )
            _persist_result(db, analysis, result, status="completed")
    except ValidationError as exc:
        logger.error(
            "Result/progress schema validation failed for %s: %s",
            analysis_id,
            format_validation_error(exc),
        )
        analysis = db.get(Analysis, uuid.UUID(analysis_id))
        if analysis and not _is_cancelled(analysis):
            result = failed_result(
                str(analysis.id),
                analysis.expires_at,
                analysis.correlation_id,
                pipeline_version=settings.pipeline_version,
            )
            try:
                _persist_result(db, analysis, result, status="failed")
            except Exception:
                logger.exception("Unable to persist failed result for %s", analysis_id)
        raise
    except Exception:
        logger.exception("Fake analysis failed for %s", analysis_id)
        analysis = db.get(Analysis, uuid.UUID(analysis_id))
        if analysis and not _is_cancelled(analysis):
            result = failed_result(
                str(analysis.id),
                analysis.expires_at,
                analysis.correlation_id,
                pipeline_version=settings.pipeline_version,
            )
            try:
                _persist_result(db, analysis, result, status="failed")
            except Exception:
                logger.exception("Unable to persist failed result for %s", analysis_id)
        raise
    finally:
        db.close()


@dramatiq.actor(max_retries=3)
def sweep_expired_analyses() -> None:
    """Mark expired analyses and enqueue deletion of their objects."""
    settings = get_settings()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        rows = (
            db.query(Analysis)
            .filter(
                Analysis.expires_at < now,
                Analysis.deleted_at.is_(None),
                Analysis.status.notin_(["deleted"]),
            )
            .limit(100)
            .all()
        )
        for analysis in rows:
            if analysis.status != "expired":
                analysis.status = "expired"
                analysis.stage = "expired"
                analysis.message_key = "expired"
                analysis.updated_at = now
            analysis.deleted_at = now
            analysis.status = "deleted"
            analysis.stage = "deleted"
            analysis.message_key = "deleted"
            analysis.result_json = None
            db.add(
                DeletionOutbox(
                    analysis_id=analysis.id,
                    object_key=analysis.source_object_key,
                )
            )
            process_deletion.send(str(analysis.id))
        if rows:
            db.commit()
            logger.info("Retention sweeper deleted %s expired analyses", len(rows))
    finally:
        db.close()

    # Self-reschedule (Dramatiq delay in ms).
    delay_ms = max(60_000, settings.retention_sweep_interval_seconds * 1000)
    sweep_expired_analyses.send_with_options(delay=delay_ms)


@dramatiq.actor(max_retries=3)
def process_deletion(analysis_id: str) -> None:
    db = SessionLocal()
    storage = ObjectStorage()
    try:
        aid = uuid.UUID(analysis_id)
        prefix = f"analyses/{analysis_id}/"
        try:
            storage.delete_prefix(prefix)
        except Exception:
            logger.exception("Object deletion failed for %s", analysis_id)

        pending = (
            db.query(DeletionOutbox)
            .filter(DeletionOutbox.analysis_id == aid, DeletionOutbox.processed_at.is_(None))
            .all()
        )
        now = datetime.now(timezone.utc)
        for row in pending:
            row.processed_at = now
        db.commit()
    finally:
        db.close()


if os.environ.get("FORMCHECK_START_SWEEPER") == "1":
    try:
        sweep_expired_analyses.send()
    except Exception:
        logger.debug("Retention sweeper not enqueued yet", exc_info=True)
