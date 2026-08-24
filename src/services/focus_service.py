"""Focus Sessions / Timer — section 26.

A logged focus session is the raw signal src/analytics/productivity.py's
deep_work_hours_per_day already reads (FocusSession.is_deep_work). The
timer itself runs client-side; the server only records completed
sessions — no server-side timer state to keep in sync.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from src.database.models import FocusSession


def log_focus_session(
    db: Session,
    user_id: str,
    duration_minutes: int,
    project_id: str | None = None,
    is_deep_work: bool = True,
    started_at: dt.datetime | None = None,
) -> FocusSession:
    session = FocusSession(
        user_id=user_id,
        project_id=project_id,
        started_at=started_at or dt.datetime.utcnow(),
        duration_minutes=duration_minutes,
        is_deep_work=is_deep_work,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_focus_sessions(db: Session, user_id: str, limit: int = 20) -> list[FocusSession]:
    return (
        db.query(FocusSession)
        .filter(FocusSession.user_id == user_id)
        .order_by(FocusSession.started_at.desc())
        .limit(limit)
        .all()
    )


def todays_focus_minutes(db: Session, user_id: str, today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    start = dt.datetime.combine(today, dt.time.min)
    end = start + dt.timedelta(days=1)
    sessions = (
        db.query(FocusSession)
        .filter(FocusSession.user_id == user_id, FocusSession.started_at >= start, FocusSession.started_at < end)
        .all()
    )
    return sum(s.duration_minutes for s in sessions)
