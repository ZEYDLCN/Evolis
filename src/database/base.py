"""SQLAlchemy engine/session setup.

Defaults to SQLite for zero-config local development. Set DATABASE_URL to a
PostgreSQL (+ pgvector) DSN for anything beyond local experimentation, e.g.:

    postgresql+psycopg://lifediff:lifediff@localhost:5432/lifediff
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lifediff.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yields a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for use outside of FastAPI (workers, scripts)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create tables. A real deployment should use Alembic migrations instead."""
    from . import models  # noqa: F401 ensure models are registered

    Base.metadata.create_all(bind=engine)
