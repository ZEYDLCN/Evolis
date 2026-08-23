"""The reward moment right after saving a daily entry — an engagement
mechanic, not part of the original spec. Turns "entry saved" from a silent
list-refresh into an immediate, specific reflection: your streak, which
topics from today are becoming a pattern this week, and which ones are
brand new. Every number here comes from the same deterministic analytics
functions used elsewhere (LLM != Analytics Engine still holds) — this
module just picks which of them are worth surfacing for *this* entry.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.analytics.streaks import StreakInfo, compute_streak
from src.database.models import Entry, EntryTopic

RECURRING_THRESHOLD = 2  # mentions this week (including today) to call out as a pattern
LOOKBACK_DAYS = 7


@dataclass
class EntryInsight:
    streak: StreakInfo
    recurring_topics: list[dict] = field(default_factory=list)  # [{"topic": str, "mentions_this_week": int}]
    new_topics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "streak": {
                "current": self.streak.current_streak,
                "longest": self.streak.longest_streak,
                "is_new_best": self.streak.is_new_best,
            },
            "recurring_topics": self.recurring_topics,
            "new_topics": self.new_topics,
        }


def build_entry_insight(db: Session, user_id: str, entry: Entry) -> EntryInsight:
    entry_date = entry.entry_date.date() if isinstance(entry.entry_date, dt.datetime) else entry.entry_date
    streak = compute_streak(db, user_id, today=entry_date)

    todays_topics = [t.topic for t in entry.topics]
    if not todays_topics:
        return EntryInsight(streak=streak)

    week_start = dt.datetime.combine(entry_date - dt.timedelta(days=LOOKBACK_DAYS - 1), dt.time.min)
    week_end = dt.datetime.combine(entry_date + dt.timedelta(days=1), dt.time.min)

    rows = db.execute(
        select(EntryTopic.topic, Entry.entry_date)
        .join(Entry, Entry.id == EntryTopic.entry_id)
        .where(Entry.user_id == user_id, Entry.entry_date >= week_start, Entry.entry_date < week_end, EntryTopic.topic.in_(todays_topics))
    ).all()

    counts: dict[str, int] = {}
    first_seen: dict[str, dt.datetime] = {}
    for topic, when in rows:
        counts[topic] = counts.get(topic, 0) + 1
        if topic not in first_seen or when < first_seen[topic]:
            first_seen[topic] = when

    recurring = [
        {"topic": topic, "mentions_this_week": count}
        for topic, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        if count >= RECURRING_THRESHOLD
    ]

    # "New" = this entry is the only sighting of it in the lookback window —
    # a real signal it wasn't already a running theme, not a guarantee it's
    # never appeared before LOOKBACK_DAYS.
    new_topics = [topic for topic in todays_topics if counts.get(topic, 0) <= 1]

    return EntryInsight(streak=streak, recurring_topics=recurring[:3], new_topics=new_topics[:3])
