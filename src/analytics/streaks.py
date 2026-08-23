"""Streak + activity heatmap — an engagement mechanic, not part of the
original spec, added because a daily-journaling product lives or dies on
whether people come back tomorrow. Pure date-set math over Entry.entry_date;
no new table, no new signal to collect.

"Streak" here means consecutive *calendar days* with at least one entry —
a user who's already logged today keeps yesterday's streak counted through
today; one who hasn't yet still sees yesterday's number (so writing today
is what extends it, not a countdown that punishes timezone edge cases).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Entry


@dataclass
class StreakInfo:
    current_streak: int
    longest_streak: int
    last_entry_date: dt.date | None
    is_new_best: bool  # current_streak just reached (or passed) longest_streak


def _entry_dates(db: Session, user_id: str) -> set[dt.date]:
    rows = db.execute(select(Entry.entry_date).where(Entry.user_id == user_id)).all()
    return {r[0].date() if isinstance(r[0], dt.datetime) else r[0] for r in rows}


def compute_streak(db: Session, user_id: str, today: dt.date | None = None) -> StreakInfo:
    today = today or dt.date.today()
    dates = _entry_dates(db, user_id)

    if not dates:
        return StreakInfo(current_streak=0, longest_streak=0, last_entry_date=None, is_new_best=False)

    # Longest streak ever: scan the sorted date set for consecutive runs.
    longest = 1
    run = 1
    ordered = sorted(dates)
    for prev, curr in zip(ordered, ordered[1:]):
        if (curr - prev).days == 1:
            run += 1
        else:
            longest = max(longest, run)
            run = 1
    longest = max(longest, run)

    # Current streak: walk backward from today (or yesterday, if nothing
    # logged today yet) while consecutive days have an entry.
    anchor = today if today in dates else today - dt.timedelta(days=1)
    current = 0
    cursor = anchor
    while cursor in dates:
        current += 1
        cursor -= dt.timedelta(days=1)

    return StreakInfo(
        current_streak=current,
        longest_streak=longest,
        last_entry_date=max(dates),
        is_new_best=current > 0 and current >= longest,
    )


def compute_heatmap(db: Session, user_id: str, days: int = 365, today: dt.date | None = None) -> list[dict]:
    """Zero-filled daily entry counts for the trailing `days` days —
    everything a GitHub-style contribution calendar needs, computed once
    here rather than the client inferring gaps from a sparse list."""
    today = today or dt.date.today()
    start = today - dt.timedelta(days=days - 1)

    # Count from raw rows, not _entry_dates' set, so a day with multiple
    # entries shows its real count rather than collapsing to 1.
    rows = db.execute(select(Entry.entry_date).where(Entry.user_id == user_id)).all()
    counts: dict[dt.date, int] = {}
    for (entry_date,) in rows:
        d = entry_date.date() if isinstance(entry_date, dt.datetime) else entry_date
        if start <= d <= today:
            counts[d] = counts.get(d, 0) + 1

    return [
        {"date": (start + dt.timedelta(days=i)).isoformat(), "count": counts.get(start + dt.timedelta(days=i), 0)}
        for i in range(days)
    ]
