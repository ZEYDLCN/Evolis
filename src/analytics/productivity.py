"""Behavioral/productivity metrics — sections 13-15.

completion_rate: derived from Entry.completion_status ("done" counts as a
completed unit of work; "partial"/"blocked"/"none" do not). A dedicated
tasks table would give a truer count; this is the MVP proxy.

context_switching: average number of distinct topics touched per active day.

deep_work: average FocusSession minutes/day where is_deep_work is true.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database.models import Entry, EntryTopic, FocusSession


def completion_rate(db: Session, user_id: str, start: dt.datetime, end: dt.datetime) -> dict:
    rows = db.execute(
        select(Entry.completion_status, func.count())
        .where(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end)
        .group_by(Entry.completion_status)
    ).all()
    counts = {status or "none": n for status, n in rows}
    total = sum(counts.values())
    done = counts.get("done", 0)
    rate = done / total if total else 0.0
    return {"created": total, "completed": done, "completion_rate": round(rate, 4)}


def context_switching_per_day(db: Session, user_id: str, start: dt.datetime, end: dt.datetime) -> float:
    rows = db.execute(
        select(Entry.entry_date, EntryTopic.topic)
        .join(EntryTopic, EntryTopic.entry_id == Entry.id)
        .where(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end)
    ).all()

    per_day: dict[dt.date, set[str]] = {}
    for entry_date, topic in rows:
        day = entry_date.date() if isinstance(entry_date, dt.datetime) else entry_date
        per_day.setdefault(day, set()).add(topic)

    if not per_day:
        return 0.0
    return round(sum(len(topics) for topics in per_day.values()) / len(per_day), 2)


def deep_work_hours_per_day(db: Session, user_id: str, start: dt.datetime, end: dt.datetime) -> float:
    rows = db.execute(
        select(FocusSession.started_at, FocusSession.duration_minutes)
        .where(
            FocusSession.user_id == user_id,
            FocusSession.started_at >= start,
            FocusSession.started_at < end,
            FocusSession.is_deep_work.is_(True),
        )
    ).all()

    per_day: dict[dt.date, int] = {}
    for started_at, minutes in rows:
        day = started_at.date() if isinstance(started_at, dt.datetime) else started_at
        per_day[day] = per_day.get(day, 0) + minutes

    if not per_day:
        return 0.0
    avg_minutes = sum(per_day.values()) / len(per_day)
    return round(avg_minutes / 60, 2)


def behavior_summary(db: Session, user_id: str, start: dt.datetime, end: dt.datetime) -> dict:
    return {
        **completion_rate(db, user_id, start, end),
        "context_switching_per_day": context_switching_per_day(db, user_id, start, end),
        "deep_work_hours_per_day": deep_work_hours_per_day(db, user_id, start, end),
    }
