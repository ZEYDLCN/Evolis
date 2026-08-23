"""Interest Drift analytics — sections 5-6.

Aggregates raw entry/topic rows into per-topic interest scores for a period.
This is the "SQL + statistics" half of the LLM != Analytics Engine principle;
the LLM is only consulted upstream (extraction) and downstream (naming an
already-discovered cluster, or explaining the numbers in prose).
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Activity, Entry, EntryTopic
from src.ml.scoring.interest_score import InterestSignal, compute_interest_score, normalize, recency_score


def topic_interest_scores(db: Session, user_id: str, start: dt.datetime, end: dt.datetime) -> dict[str, float]:
    rows = (
        db.execute(
            select(EntryTopic.topic, Entry.entry_date)
            .join(Entry, Entry.id == EntryTopic.entry_id)
            .where(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end)
        )
        .all()
    )

    mentions: dict[str, int] = defaultdict(int)
    last_seen: dict[str, dt.datetime] = {}
    for topic, entry_date in rows:
        mentions[topic] += 1
        if topic not in last_seen or entry_date > last_seen[topic]:
            last_seen[topic] = entry_date

    durations: dict[str, int] = defaultdict(int)
    activity_rows = (
        db.execute(
            select(Activity.topic, Activity.duration_minutes)
            .join(Entry, Entry.id == Activity.entry_id)
            .where(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end)
        )
        .all()
    )
    for topic, minutes in activity_rows:
        if topic and minutes:
            durations[topic] += minutes

    project_usage: dict[str, int] = defaultdict(int)
    project_rows = (
        db.execute(
            select(Activity.topic)
            .join(Entry, Entry.id == Activity.entry_id)
            .where(
                Entry.user_id == user_id,
                Entry.entry_date >= start,
                Entry.entry_date < end,
                Activity.project_id.is_not(None),
            )
        )
        .all()
    )
    for (topic,) in project_rows:
        if topic:
            project_usage[topic] += 1

    if not mentions:
        return {}

    max_mentions = max(mentions.values())
    max_duration = max(durations.values()) if durations else 0
    max_project_usage = max(project_usage.values()) if project_usage else 0
    now = end

    scores: dict[str, float] = {}
    for topic, count in mentions.items():
        days_since = (now - last_seen[topic]).days
        signal = InterestSignal(
            normalized_mentions=normalize(count, max_mentions),
            normalized_duration=normalize(durations.get(topic, 0), max_duration),
            recency_score=recency_score(max(days_since, 0)),
            project_usage=normalize(project_usage.get(topic, 0), max_project_usage),
            learning_frequency=normalize(count, max_mentions),  # proxy until dedicated event log exists
        )
        scores[topic] = round(compute_interest_score(signal), 4)

    return dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))
