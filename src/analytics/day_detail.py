"""Daily Detail Page — sections 18-19.

Pure aggregation over a single calendar day: which entries were written,
what topics/activities they broke down into, and total focused minutes.
No LLM involved — every number here comes straight from the extraction
already stored on Entry/Activity/EntryTopic.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy.orm import Session

from src.database.models import Activity, Entry, EntryTopic


def build_day_detail(db: Session, user_id: str, day: dt.date) -> dict:
    start = dt.datetime.combine(day, dt.time.min)
    end = start + dt.timedelta(days=1)

    entries = (
        db.query(Entry)
        .filter(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end)
        .order_by(Entry.entry_date)
        .all()
    )

    entry_payloads = []
    minutes_by_topic: dict[str, int] = defaultdict(int)
    total_minutes = 0

    for entry in entries:
        topics = [t.topic for t in db.query(EntryTopic).filter(EntryTopic.entry_id == entry.id).all()]
        activities = db.query(Activity).filter(Activity.entry_id == entry.id).all()
        for activity in activities:
            minutes = activity.duration_minutes or 0
            total_minutes += minutes
            if activity.topic:
                minutes_by_topic[activity.topic] += minutes

        entry_payloads.append(
            {
                "id": entry.id,
                "text": entry.raw_text,
                "completion_status": entry.completion_status,
                "blockers": entry.blockers or [],
                "topics": topics,
                "activities": [
                    {"type": a.type, "topic": a.topic, "duration_minutes": a.duration_minutes} for a in activities
                ],
            }
        )

    return {
        "date": day.isoformat(),
        "entries": entry_payloads,
        "entry_count": len(entries),
        "focused_minutes": total_minutes,
        "topic_breakdown": dict(sorted(minutes_by_topic.items(), key=lambda kv: kv[1], reverse=True)),
    }
