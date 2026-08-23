"""Anomaly Detection — section 17.

Wires src/ml/anomaly/anomaly_detector.py (pure math, no DB) to real learning
time. Compares the current week's total learning minutes (across all
topics, and per-topic) against the trailing 8-week baseline via rolling
mean + z-score.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.analytics.temporal import period_bounds
from src.database.models import Activity, Entry
from src.ml.anomaly.anomaly_detector import Anomaly, detect_zscore_anomaly

LOOKBACK_WEEKS = 8


def _weekly_learning_minutes(db: Session, user_id: str, week_start: dt.datetime, week_end: dt.datetime) -> dict[str, int]:
    """Total learning-activity minutes for the week, overall ("_total") and per topic."""
    rows = db.execute(
        select(Activity.topic, Activity.duration_minutes)
        .join(Entry, Entry.id == Activity.entry_id)
        .where(
            Entry.user_id == user_id,
            Entry.entry_date >= week_start,
            Entry.entry_date < week_end,
            Activity.type == "learning",
        )
    ).all()

    minutes_by_topic: dict[str, int] = defaultdict(int)
    for topic, minutes in rows:
        if minutes:
            minutes_by_topic["_total"] += minutes
            if topic:
                minutes_by_topic[topic] += minutes
    return dict(minutes_by_topic)


def detect_learning_time_anomalies(db: Session, user_id: str, now: dt.datetime | None = None) -> list[Anomaly]:
    now = now or dt.datetime.utcnow()
    current_start, current_end = period_bounds("weekly", now.date())

    history_by_topic: dict[str, list[float]] = defaultdict(list)
    for i in range(1, LOOKBACK_WEEKS + 1):
        past_anchor = (current_start - dt.timedelta(weeks=i)).date()
        past_start, past_end = period_bounds("weekly", past_anchor)
        for topic, minutes in _weekly_learning_minutes(db, user_id, past_start, past_end).items():
            history_by_topic[topic].append(float(minutes))

    current = _weekly_learning_minutes(db, user_id, current_start, current_end)

    anomalies: list[Anomaly] = []
    for topic, current_minutes in current.items():
        history = history_by_topic.get(topic, [])
        # Zero-fill weeks where this topic didn't appear at all, so a brand
        # new obsession reads as a real spike rather than "no history".
        history = history + [0.0] * (LOOKBACK_WEEKS - len(history))
        label = "Total learning time" if topic == "_total" else topic
        anomaly = detect_zscore_anomaly(label, float(current_minutes), history)
        if anomaly:
            anomalies.append(anomaly)

    return anomalies
