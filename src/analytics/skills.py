"""Skill Evolution + Skill Graph aggregation — sections 10-11."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Activity, Entry
from src.ml.scoring.skill_score import SkillSignal, compute_skill_score


def skill_scores(db: Session, user_id: str, start: dt.datetime, end: dt.datetime) -> list[dict]:
    rows = (
        db.execute(
            select(Activity.type, Activity.topic, Activity.project_id, Entry.entry_date)
            .join(Entry, Entry.id == Activity.entry_id)
            .where(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end, Activity.topic.is_not(None))
        )
        .all()
    )

    learning = defaultdict(int)
    practice = defaultdict(int)
    project_usage = defaultdict(int)
    last_seen: dict[str, dt.datetime] = {}
    first_seen: dict[str, dt.datetime] = {}

    for activity_type, topic, project_id, entry_date in rows:
        if activity_type == "learning":
            learning[topic] += 1
        else:
            practice[topic] += 1
        if project_id:
            project_usage[topic] += 1
        if topic not in first_seen or entry_date < first_seen[topic]:
            first_seen[topic] = entry_date
        if topic not in last_seen or entry_date > last_seen[topic]:
            last_seen[topic] = entry_date

    all_topics = set(learning) | set(practice)
    if not all_topics:
        return []

    max_learning = max(learning.values(), default=1) or 1
    max_practice = max(practice.values(), default=1) or 1
    max_project = max(project_usage.values(), default=1) or 1
    now = end

    results = []
    for topic in all_topics:
        days_since = (now - last_seen[topic]).days
        recency = max(0.0, 1 - days_since / 30)
        signal = SkillSignal(
            learning_frequency=min(1.0, learning[topic] / max_learning),
            practice_frequency=min(1.0, practice[topic] / max_practice),
            project_usage=min(1.0, project_usage.get(topic, 0) / max_project),
            completion_events=min(1.0, practice[topic] / max_practice),  # proxy signal
            recency=recency,
        )
        results.append(
            {
                "skill": topic,
                "activity_score": compute_skill_score(signal),
                "first_seen": first_seen[topic].isoformat(),
                "last_seen": last_seen[topic].isoformat(),
                "project_usage": project_usage.get(topic, 0),
                "learning_sessions": learning.get(topic, 0),
            }
        )

    return sorted(results, key=lambda r: r["activity_score"], reverse=True)
