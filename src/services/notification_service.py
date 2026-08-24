"""Notification Center — section 33.

Deliberately not a stored/dismissable inbox: every notification here is
re-derived on each request from analytics that already exist elsewhere
(anomalies, patterns, goal suggestions). That keeps it always accurate to
the user's current data with zero new state to keep in sync, at the cost
of no read/unread tracking — an acceptable trade at this stage; a real
inbox (with dismissal) would need a stored Notification table instead.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from src.analytics.anomalies import detect_learning_time_anomalies
from src.analytics.patterns import detect_project_load_vs_completion
from src.services.goal_service import suggest_goals


def build_notifications(db: Session, user_id: str, now: dt.datetime | None = None) -> list[dict]:
    now = now or dt.datetime.utcnow()
    notifications: list[dict] = []

    for anomaly in detect_learning_time_anomalies(db, user_id, now):
        direction = "spiked" if anomaly.z_score > 0 else "dropped"
        notifications.append(
            {
                "type": "anomaly",
                "title": f"{anomaly.metric} {direction}",
                "detail": f"{round(anomaly.current_value)} min this week vs ~{round(anomaly.baseline_mean)} min average.",
                "confidence": anomaly.confidence,
            }
        )

    finding = detect_project_load_vs_completion(db, user_id, now)
    if finding:
        notifications.append(
            {
                "type": "pattern",
                "title": "New pattern detected",
                "detail": finding.description,
                "confidence": finding.confidence,
            }
        )

    for suggestion in suggest_goals(db, user_id, now)[:2]:
        notifications.append(
            {
                "type": "goal_suggestion",
                "title": suggestion["title"],
                "detail": suggestion["description"],
                "confidence": "medium",
            }
        )

    return notifications
