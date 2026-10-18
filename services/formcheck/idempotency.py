"""Idempotency-Key helpers for create and delete."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from formcheck.models import IdempotencyKey


def hash_request_body(payload: dict[str, Any] | None) -> str:
    canonical = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def lookup_idempotency(
    db: Session,
    *,
    key: str | None,
    route: str,
    request_hash: str,
) -> IdempotencyKey | None:
    if not key:
        return None
    if len(key) > 128:
        raise HTTPException(status_code=400, detail="Idempotency-Key too long")
    row = db.get(IdempotencyKey, {"key": key, "route": route})
    if row is None:
        return None
    if row.request_hash != request_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key reused with a different request body",
        )
    return row


def store_idempotency(
    db: Session,
    *,
    key: str | None,
    route: str,
    request_hash: str,
    response_status: int,
    response_body: dict[str, Any] | None,
    analysis_id: Any = None,
) -> None:
    if not key:
        return
    existing = db.get(IdempotencyKey, {"key": key, "route": route})
    if existing is not None:
        return
    db.add(
        IdempotencyKey(
            key=key,
            route=route,
            request_hash=request_hash,
            response_status=response_status,
            response_body=response_body,
            analysis_id=analysis_id,
        )
    )
