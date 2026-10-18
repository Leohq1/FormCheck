from collections.abc import Generator
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from formcheck.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _engine():
    return create_engine(get_settings().database_url, pool_pre_ping=True)


engine = _engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations() -> None:
    """Apply Alembic migrations to head."""
    from alembic import command
    from alembic.config import Config
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", get_settings().database_url)
    command.upgrade(cfg, "head")


def init_db() -> None:
    from formcheck import models  # noqa: F401

    try:
        run_migrations()
    except Exception:
        logger.exception("Alembic migrate failed; falling back to create_all for local boot")
        Base.metadata.create_all(bind=engine)
