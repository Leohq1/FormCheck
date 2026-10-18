"""API integration fixtures using SQLite + dependency overrides."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, String, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from formcheck.auth import generate_capability_token, hash_capability_token
from formcheck.db import Base, get_db
from formcheck.models import Analysis, AuditEvent, DeletionOutbox, IdempotencyKey


class GUID(TypeDecorator):
    """UUID stored as CHAR for SQLite tests."""

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _prepare_sqlite_metadata() -> None:
    for table in (
        Analysis.__table__,
        AuditEvent.__table__,
        DeletionOutbox.__table__,
        IdempotencyKey.__table__,
    ):
        for column in table.columns:
            type_name = type(column.type).__name__
            if type_name in {"UUID", "GUID"}:
                column.type = GUID()
            elif type_name == "JSONB":
                column.type = JSON()


@pytest.fixture()
def db_session():
    _prepare_sqlite_metadata()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def storage_mock():
    mock = MagicMock()
    mock.presign_put.return_value = "http://localhost:9000/formcheck/upload"
    mock.stat_object.return_value = MagicMock(size=1024, content_type="video/mp4", etag="x")
    mock.object_exists.return_value = True
    mock.delete_prefix.return_value = []
    return mock


@pytest.fixture()
def client(db_session: Session, storage_mock: MagicMock, monkeypatch: pytest.MonkeyPatch):
    from formcheck.api import main as main_mod
    from formcheck.api import routes as routes_mod
    from formcheck.worker import tasks as tasks_mod

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    main_mod.app.router.lifespan_context = _noop_lifespan

    def _override_db():
        try:
            yield db_session
        finally:
            pass

    main_mod.app.dependency_overrides[get_db] = _override_db
    monkeypatch.setattr(routes_mod, "ObjectStorage", lambda *a, **k: storage_mock)
    monkeypatch.setattr(routes_mod, "rewrite_presign_host_for_browser", lambda url, *_: url)
    monkeypatch.setattr(tasks_mod.run_fake_analysis, "send", MagicMock())
    monkeypatch.setattr(tasks_mod.process_deletion, "send", MagicMock())

    with TestClient(main_mod.app, raise_server_exceptions=True) as test_client:
        yield test_client

    main_mod.app.dependency_overrides.clear()


@pytest.fixture()
def seeded_analysis(db_session: Session) -> tuple[Analysis, str]:
    token = generate_capability_token()
    analysis = Analysis(
        id=uuid.uuid4(),
        token_hash=hash_capability_token(token),
        status="queued",
        stage="queued",
        progress=None,
        message_key="queued",
        stroke="overhead_clear",
        handedness="right",
        view_hint="side",
        consent=True,
        filename="clear.mp4",
        content_type="video/mp4",
        byte_size=1024,
        source_object_key="analyses/x/source/clear.mp4",
        upload_completed=True,
        pipeline_version="2026.10.0",
        correlation_id="corr-test",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(analysis)
    db_session.commit()
    return analysis, token
