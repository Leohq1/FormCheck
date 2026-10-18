from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from formcheck.config import get_settings


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


def init_db() -> None:
    from formcheck import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
