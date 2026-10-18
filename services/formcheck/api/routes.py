from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from fastapi.responses import JSONResponse
from jsonschema import ValidationError
from sqlalchemy.orm import Session

from formcheck.api.deps import get_analysis_for_token, get_analysis_for_token_including_deleted
from formcheck.auth import generate_capability_token, hash_capability_token
from formcheck.compat import to_interim_result
from formcheck.config import get_settings
from formcheck.contract_validate import (
    format_validation_error,
    validate_analysis_result,
)
from formcheck.db import get_db
from formcheck.idempotency import hash_request_body, lookup_idempotency, store_idempotency
from formcheck.models import Analysis, AuditEvent, DeletionOutbox
from formcheck.schemas import (
    RESULT_READY_STATUSES,
    TERMINAL_STATUSES,
    AnalysisJob,
    AnalysisProgress,
    AnalysisResult,
    CompleteUploadResponse,
    CreateAnalysisRequest,
    CreateAnalysisResponse,
)
from formcheck.storage import ObjectStorage, rewrite_presign_host_for_browser, source_object_key
from formcheck.worker.tasks import process_deletion, run_fake_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

ALLOWED_CONTENT_TYPES = {"video/mp4", "video/quicktime"}
ALLOWED_EXTENSIONS = {".mp4", ".mov"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_create(body: CreateAnalysisRequest) -> None:
    settings = get_settings()
    if not body.consent:
        raise HTTPException(status_code=400, detail="Consent is required")
    if body.byte_size > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="File exceeds maximum size")
    if body.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported content type")
    lower = body.filename.lower()
    if not any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Unsupported file extension")
    if re.search(r"[\\/]", body.filename):
        raise HTTPException(status_code=400, detail="Invalid filename")


def _audit(
    db: Session,
    analysis_id: uuid.UUID | None,
    event: str,
    correlation_id: str,
    details: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            analysis_id=analysis_id,
            event=event,
            correlation_id=correlation_id,
            details=details,
        )
    )


def _build_job(analysis: Analysis) -> dict[str, Any]:
    job = AnalysisJob(
        schema_version="1",
        analysis_id=str(analysis.id),
        video_object_key=analysis.source_object_key,
        stroke=analysis.stroke,  # type: ignore[arg-type]
        handedness=analysis.handedness,  # type: ignore[arg-type]
        view_hint=analysis.view_hint,  # type: ignore[arg-type]
        pipeline_version=analysis.pipeline_version,
    )
    return job.model_dump()


@router.post("/analyses", response_model=CreateAnalysisResponse, status_code=status.HTTP_201_CREATED)
def create_analysis(
    body: CreateAnalysisRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> CreateAnalysisResponse | JSONResponse:
    _validate_create(body)
    settings = get_settings()
    route = "POST /api/v1/analyses"
    req_hash = hash_request_body(body.model_dump())
    cached = lookup_idempotency(db, key=idempotency_key, route=route, request_hash=req_hash)
    if cached is not None and cached.response_body is not None:
        return JSONResponse(status_code=cached.response_status, content=cached.response_body)

    storage = ObjectStorage(settings)

    analysis_id = uuid.uuid4()
    token = generate_capability_token()
    object_key = source_object_key(str(analysis_id), body.filename)
    correlation_id = f"corr-{str(analysis_id)[:8]}"
    expires_at = _utc_now() + timedelta(hours=settings.retention_hours)

    upload_url = storage.presign_put(object_key, body.content_type)
    upload_url = rewrite_presign_host_for_browser(upload_url, settings.minio_public_endpoint)

    analysis = Analysis(
        id=analysis_id,
        token_hash=hash_capability_token(token),
        status="created",
        stage="created",
        progress=None,
        message_key="awaiting_upload",
        stroke=body.stroke,
        handedness=body.handedness,
        view_hint=body.view_hint,
        consent=body.consent,
        filename=body.filename,
        content_type=body.content_type,
        byte_size=body.byte_size,
        source_object_key=object_key,
        upload_completed=False,
        pipeline_version=settings.pipeline_version,
        correlation_id=correlation_id,
        expires_at=expires_at,
    )
    db.add(analysis)
    response = CreateAnalysisResponse(
        schema_version=settings.schema_version,
        analysis_id=str(analysis_id),
        capability_token=token,
        upload_url=upload_url,
        status="created",
    )
    store_idempotency(
        db,
        key=idempotency_key,
        route=route,
        request_hash=req_hash,
        response_status=201,
        response_body=response.model_dump(),
        analysis_id=analysis_id,
    )
    _audit(db, analysis_id, "analysis.created", correlation_id, {"stroke": body.stroke})
    db.commit()
    return response


@router.post(
    "/analyses/{analysis_id}/complete-upload",
    response_model=CompleteUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def complete_upload(
    analysis_id: uuid.UUID,
    analysis: Analysis = Depends(get_analysis_for_token),
    db: Session = Depends(get_db),
) -> CompleteUploadResponse:
    settings = get_settings()

    if analysis.upload_completed and analysis.status not in {"created", "uploading"}:
        return CompleteUploadResponse(
            schema_version=settings.schema_version,
            analysis_id=str(analysis.id),
            status=analysis.status,  # type: ignore[arg-type]
        )

    storage = ObjectStorage(settings)
    try:
        stat = storage.stat_object(analysis.source_object_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail="Uploaded object not found") from exc

    if stat.size == 0:
        raise HTTPException(status_code=400, detail="Uploaded object is empty")
    if analysis.byte_size > 0 and stat.size > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="Uploaded object exceeds size limit")

    analysis.upload_completed = True
    analysis.status = "queued"
    analysis.stage = "queued"
    analysis.message_key = "queued"
    analysis.progress = None
    analysis.updated_at = _utc_now()
    _audit(
        db,
        analysis.id,
        "analysis.upload_completed",
        analysis.correlation_id,
        {"size": stat.size},
    )
    db.commit()

    job = _build_job(analysis)
    run_fake_analysis.send(job)

    return CompleteUploadResponse(
        schema_version=settings.schema_version,
        analysis_id=str(analysis.id),
        status="queued",
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisProgress)
def get_analysis(
    analysis: Analysis = Depends(get_analysis_for_token),
) -> AnalysisProgress:
    settings = get_settings()
    now = _utc_now()
    status_value = analysis.status
    expires = analysis.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now and status_value not in TERMINAL_STATUSES | {"deleted"}:
        status_value = "expired"

    return AnalysisProgress(
        schema_version=settings.schema_version,
        analysis_id=str(analysis.id),
        status=status_value,  # type: ignore[arg-type]
        stage=analysis.stage,
        progress=analysis.progress,
        message_key=analysis.message_key,
        updated_at=_iso(analysis.updated_at) or _iso(now) or "",
        expires_at=_iso(analysis.expires_at),
    )


@router.get("/analyses/{analysis_id}/result")
def get_result(
    analysis: Analysis = Depends(get_analysis_for_token),
) -> dict[str, Any]:
    settings = get_settings()
    now = _utc_now()
    expires = analysis.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Expired")

    if analysis.status not in RESULT_READY_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Result not ready")

    if not analysis.result_json:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Result not ready")

    payload = dict(analysis.result_json)
    try:
        validate_analysis_result(payload)
    except ValidationError as exc:
        logger.error("Stored result failed schema validation: %s", format_validation_error(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored result failed contract validation",
        ) from exc

    # Always ensure Pydantic ratified model accepts the payload.
    AnalysisResult.model_validate(payload)

    if settings.interim_result_shim:
        return to_interim_result(payload)
    return payload


@router.post(
    "/analyses/{analysis_id}/cancel",
    response_model=AnalysisProgress,
    status_code=status.HTTP_202_ACCEPTED,
)
def cancel_analysis(
    analysis: Analysis = Depends(get_analysis_for_token),
    db: Session = Depends(get_db),
) -> AnalysisProgress:
    """Cooperative cancel — worker stops between stages; objects retained until delete/expiry."""
    settings = get_settings()
    if analysis.status in {"deleted"}:
        raise HTTPException(status_code=410, detail="Analysis deleted")
    if analysis.status in {"completed", "inconclusive", "failed", "expired", "cancelled"}:
        return AnalysisProgress(
            schema_version=settings.schema_version,
            analysis_id=str(analysis.id),
            status=analysis.status,  # type: ignore[arg-type]
            stage=analysis.stage,
            progress=analysis.progress,
            message_key=analysis.message_key,
            updated_at=_iso(analysis.updated_at) or _iso(_utc_now()) or "",
            expires_at=_iso(analysis.expires_at),
        )

    analysis.status = "cancelled"
    analysis.stage = "cancelled"
    analysis.message_key = "cancelled"
    analysis.updated_at = _utc_now()
    _audit(db, analysis.id, "analysis.cancelled", analysis.correlation_id)
    db.commit()

    return AnalysisProgress(
        schema_version=settings.schema_version,
        analysis_id=str(analysis.id),
        status="cancelled",
        stage="cancelled",
        progress=analysis.progress,
        message_key="cancelled",
        updated_at=_iso(analysis.updated_at) or "",
        expires_at=_iso(analysis.expires_at),
    )


@router.delete("/analyses/{analysis_id}", status_code=status.HTTP_202_ACCEPTED)
def delete_analysis(
    analysis: Analysis = Depends(get_analysis_for_token_including_deleted),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> Response:
    route = f"DELETE /api/v1/analyses/{analysis.id}"
    req_hash = hash_request_body({"analysis_id": str(analysis.id)})
    cached = lookup_idempotency(db, key=idempotency_key, route=route, request_hash=req_hash)
    if cached is not None:
        return Response(status_code=cached.response_status)

    if analysis.deleted_at is not None or analysis.status == "deleted":
        store_idempotency(
            db,
            key=idempotency_key,
            route=route,
            request_hash=req_hash,
            response_status=202,
            response_body=None,
            analysis_id=analysis.id,
        )
        db.commit()
        return Response(status_code=status.HTTP_202_ACCEPTED)

    analysis.status = "deleted"
    analysis.stage = "deleted"
    analysis.message_key = "deleted"
    analysis.deleted_at = _utc_now()
    analysis.result_json = None
    db.add(
        DeletionOutbox(
            analysis_id=analysis.id,
            object_key=analysis.source_object_key,
        )
    )
    store_idempotency(
        db,
        key=idempotency_key,
        route=route,
        request_hash=req_hash,
        response_status=202,
        response_body=None,
        analysis_id=analysis.id,
    )
    _audit(db, analysis.id, "analysis.deleted", analysis.correlation_id)
    db.commit()

    process_deletion.send(str(analysis.id))
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
