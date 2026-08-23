"""ORM models for Evolis.

Tables map directly onto the schema sketched in docs/ARCHITECTURE.md (section
"Database"): users, entries, entry_topics, activities, projects, skills,
goals, embeddings, clusters, versions, version_metrics, insights,
focus_sessions, tasks.

Embeddings are stored as JSON float arrays by default so the whole stack runs
on SQLite with zero setup. When DATABASE_URL points at Postgres and pgvector
is installed, EMBEDDING_BACKEND=pgvector switches the `vector` column to a
real `vector` type for ANN search.
"""
from __future__ import annotations

import datetime as dt
import os
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .encryption import EncryptedText

USE_PGVECTOR = os.getenv("EMBEDDING_BACKEND", "json") == "pgvector"

if USE_PGVECTOR:
    from pgvector.sqlalchemy import Vector

    VectorType = Vector(1024)
else:
    VectorType = JSON


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> dt.datetime:
    return dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Nullable: a Google-only account (see src/services/auth_service.py's
    # Google sign-in path) has no password to check — it can only ever log
    # in via Google. A password-based account never has google_sub set.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    entries: Mapped[list["Entry"]] = relationship(back_populates="user")
    projects: Mapped[list["Project"]] = relationship(back_populates="user")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user")
    versions: Mapped[list["Version"]] = relationship(back_populates="user")


class Entry(Base):
    """One daily natural-language check-in."""

    __tablename__ = "entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    raw_text: Mapped[str] = mapped_column(EncryptedText)
    entry_date: Mapped[dt.date] = mapped_column(DateTime, default=_now)
    completion_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    blockers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    extraction_raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="entries")
    topics: Mapped[list["EntryTopic"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    activities: Mapped[list["Activity"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    embedding: Mapped["Embedding | None"] = relationship(back_populates="entry", uselist=False, cascade="all, delete-orphan")


class EntryTopic(Base):
    """Topic mentions extracted from an entry (many-to-many, denormalized)."""

    __tablename__ = "entry_topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entry_id: Mapped[str] = mapped_column(ForeignKey("entries.id"), index=True)
    topic: Mapped[str] = mapped_column(String(120), index=True)
    cluster_id: Mapped[str | None] = mapped_column(ForeignKey("clusters.id"), nullable=True)

    entry: Mapped["Entry"] = relationship(back_populates="topics")
    cluster: Mapped["Cluster | None"] = relationship(back_populates="topics")


class Activity(Base):
    """A structured activity extracted from an entry (learning, project work, ...)."""

    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entry_id: Mapped[str] = mapped_column(ForeignKey("entries.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))  # learning | project_development | practice | ...
    topic: Mapped[str | None] = mapped_column(String(120), nullable=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    entry: Mapped["Entry"] = relationship(back_populates="activities")
    project: Mapped["Project | None"] = relationship(back_populates="activities")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="projects")
    activities: Mapped[list["Activity"]] = relationship(back_populates="project")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    first_seen: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)
    last_seen: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="goals")


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entry_id: Mapped[str] = mapped_column(ForeignKey("entries.id"), unique=True, index=True)
    model_name: Mapped[str] = mapped_column(String(120))
    vector: Mapped[list] = mapped_column(VectorType)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    entry: Mapped["Entry"] = relationship(back_populates="embedding")


class Cluster(Base):
    """A semantic topic cluster discovered by HDBSCAN over entry embeddings."""

    __tablename__ = "clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    representative_topics: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    topics: Mapped[list["EntryTopic"]] = relationship(back_populates="cluster")


class Version(Base):
    """A periodic (weekly/monthly/custom) snapshot of the user's profile."""

    __tablename__ = "versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(20))  # e.g. "1.7"
    period_start: Mapped[dt.date] = mapped_column(DateTime)
    period_end: Mapped[dt.date] = mapped_column(DateTime)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="versions")
    metrics: Mapped[list["VersionMetric"]] = relationship(back_populates="version", cascade="all, delete-orphan")


class VersionMetric(Base):
    """Key/value metrics attached to a version snapshot (flexible schema)."""

    __tablename__ = "version_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    version_id: Mapped[str] = mapped_column(ForeignKey("versions.id"), index=True)
    key: Mapped[str] = mapped_column(String(80))
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    version: Mapped["Version"] = relationship(back_populates="metrics")


class Insight(Base):
    """Generated observations (patterns, anomalies, release notes)."""

    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))  # pattern | anomaly | release_note | qa
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class Task(Base):
    """Explicit created/completed task tracking for a truer completion rate
    than the Entry.completion_status proxy (section 13).

    Optional by design: a user who never creates a Task still gets a
    completion rate computed from entry status (see
    src/analytics/productivity.py). Once tasks exist for a period, they take
    over as the source of truth for that period.
    """

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    entry_id: Mapped[str | None] = mapped_column(ForeignKey("entries.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | done
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    is_deep_work: Mapped[bool] = mapped_column(Boolean, default=True)
