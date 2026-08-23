"""Version Generation — section 26.

Aggregates a period's metrics into a Version + VersionMetric rows. Meant to
be called from the monthly/weekly scheduler (Celery beat) or on demand via
POST /versions/generate.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from src.analytics.interests import topic_interest_scores
from src.analytics.productivity import behavior_summary
from src.analytics.skills import skill_scores
from src.database.models import Version, VersionMetric


def _next_label(db: Session, user_id: str) -> str:
    count = db.query(Version).filter(Version.user_id == user_id).count()
    return f"1.{count}"


def generate_version(db: Session, user_id: str, start: dt.datetime, end: dt.datetime, label: str | None = None) -> Version:
    version = Version(
        user_id=user_id,
        label=label or _next_label(db, user_id),
        period_start=start,
        period_end=end,
    )
    db.add(version)
    db.flush()  # get version.id

    interests = topic_interest_scores(db, user_id, start, end)
    skills = skill_scores(db, user_id, start, end)
    behavior = behavior_summary(db, user_id, start, end)

    top_topics = list(interests.keys())[:10]

    metrics = [
        VersionMetric(version_id=version.id, key="top_topics", value_json=top_topics),
        VersionMetric(version_id=version.id, key="topic_scores", value_json=interests),
        VersionMetric(version_id=version.id, key="skill_scores", value_json=skills),
        VersionMetric(version_id=version.id, key="completion_rate", value_number=behavior["completion_rate"]),
        VersionMetric(version_id=version.id, key="context_switching_per_day", value_number=behavior["context_switching_per_day"]),
        VersionMetric(version_id=version.id, key="deep_work_hours_per_day", value_number=behavior["deep_work_hours_per_day"]),
    ]
    db.add_all(metrics)
    db.commit()
    db.refresh(version)
    return version


def version_metrics_dict(version: Version) -> dict:
    out: dict = {}
    for m in version.metrics:
        out[m.key] = m.value_json if m.value_json is not None else m.value_number
    return out
