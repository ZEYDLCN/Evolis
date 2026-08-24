"""Evolis Score — section 10.

Deliberately four separate signals, never one blended "life score": a
single number is what the proposal itself calls out as artificial and
misleading. Every formula here is fixed and deterministic (LLM != Analytics
Engine) — the same LLM! = Analytics Engine principle as everywhere else in
this codebase.

    Consistency — how many of the last 30 days had an entry, with a mild
                  bonus for the current streak (shows up faster than the
                  raw ratio alone would).
    Focus       — deep work relative to a realistic daily target, balanced
                  against low context switching.
    Execution   — the same completion_rate already computed in
                  src/analytics/productivity.py, just rescaled to 0-100.
    Learning    — how much dedicated "learning"-type activity happened,
                  relative to a realistic monthly target.

Targets (below) are working assumptions, not universal truths — tune them
once real usage data exists.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.analytics.productivity import behavior_summary
from src.analytics.streaks import compute_streak
from src.database.models import Activity, Entry

WINDOW_DAYS = 30
DEEP_WORK_TARGET_HOURS = 3.0  # hours/day considered "excellent" focus
CONTEXT_SWITCH_CEILING = 8.0  # switches/day considered maximally scattered
LEARNING_SESSIONS_TARGET = 12  # learning-type activities/month considered excellent
STREAK_BONUS_CAP = 10  # max points consistency can gain from an active streak


@dataclass
class EvolisScore:
    consistency: int
    focus: int
    execution: int
    learning: int

    def to_dict(self) -> dict:
        return {"consistency": self.consistency, "focus": self.focus, "execution": self.execution, "learning": self.learning}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _consistency(db: Session, user_id: str, now: dt.datetime) -> int:
    start = now - dt.timedelta(days=WINDOW_DAYS)
    rows = db.execute(select(Entry.entry_date).where(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < now)).all()
    active_days = len({(d.date() if isinstance(d, dt.datetime) else d) for (d,) in rows})

    base = (active_days / WINDOW_DAYS) * 100
    streak = compute_streak(db, user_id, today=now.date())
    bonus = min(STREAK_BONUS_CAP, streak.current_streak)
    return round(_clamp(base + bonus))


def _focus(db: Session, user_id: str, now: dt.datetime) -> int:
    start = now - dt.timedelta(days=WINDOW_DAYS)
    behavior = behavior_summary(db, user_id, start, now)

    deep_work_score = _clamp((behavior["deep_work_hours_per_day"] / DEEP_WORK_TARGET_HOURS) * 100)
    switching_score = _clamp(100 - (behavior["context_switching_per_day"] / CONTEXT_SWITCH_CEILING) * 100)
    return round((deep_work_score + switching_score) / 2)


def _execution(db: Session, user_id: str, now: dt.datetime) -> int:
    start = now - dt.timedelta(days=WINDOW_DAYS)
    behavior = behavior_summary(db, user_id, start, now)
    return round(_clamp(behavior["completion_rate"] * 100))


def _learning(db: Session, user_id: str, now: dt.datetime) -> int:
    start = now - dt.timedelta(days=WINDOW_DAYS)
    count = (
        db.query(Activity)
        .join(Entry, Entry.id == Activity.entry_id)
        .filter(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < now, Activity.type == "learning")
        .count()
    )
    return round(_clamp((count / LEARNING_SESSIONS_TARGET) * 100))


def compute_evolis_score(db: Session, user_id: str, now: dt.datetime | None = None) -> EvolisScore:
    now = now or dt.datetime.utcnow()
    return EvolisScore(
        consistency=_consistency(db, user_id, now),
        focus=_focus(db, user_id, now),
        execution=_execution(db, user_id, now),
        learning=_learning(db, user_id, now),
    )
