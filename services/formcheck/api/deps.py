from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from formcheck.auth import tokens_match
from formcheck.db import get_db
from formcheck.models import Analysis


def extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return token


def get_analysis_for_token(
    analysis_id: uuid.UUID,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Analysis:
    token = extract_bearer(authorization)
    analysis = db.get(Analysis, analysis_id)
    # Uniform not-found for missing id or bad token (privacy)
    if analysis is None or analysis.deleted_at is not None or not tokens_match(token, analysis.token_hash):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return analysis
