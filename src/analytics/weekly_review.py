"""Weekly Review — section 11: the "come back every Sunday" feature.

Reuses the same building blocks as the dashboard (behavior_summary,
topic_interest_scores, the weekly-evolution delta calc) rather than
inventing parallel metrics — a user's weekly number and their dashboard
number for the same thing should never disagree.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.analytics.dashboard import weekly_behavior_deltas
from src.analytics.interests import topic_interest_scores
from src.analytics.productivity import behavior_summary
from src.analytics.temporal import period_bounds
from src.database.models import Activity, Entry


@dataclass
class WeeklyReview:
    period_start: str
    period_end: str
    entries_count: int
    learning_hours: float
    projects_touched: int
    completion_rate: float
    top_focus: str | None
    emerging_topic: str | None
    biggest_improvement: dict | None
    watch: dict | None

    def to_dict(self) -> dict:
        return {
            "period_start": self.period_start,
            "period_end": self.period_end,
            "entries_count": self.entries_count,
            "learning_hours": self.learning_hours,
            "projects_touched": self.projects_touched,
            "completion_rate": self.completion_rate,
            "top_focus": self.top_focus,
            "emerging_topic": self.emerging_topic,
            "biggest_improvement": self.biggest_improvement,
            "watch": self.watch,
        }


def build_weekly_review(db: Session, user_id: str, now: dt.datetime | None = None) -> WeeklyReview:
    now = now or dt.datetime.utcnow()
    start, end = period_bounds("weekly", now.date())
    prev_start, prev_end = period_bounds("weekly", (now - dt.timedelta(days=7)).date())

    entries_count = db.query(Entry).filter(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end).count()

    learning_minutes = (
        db.query(Activity.duration_minutes)
        .join(Entry, Entry.id == Activity.entry_id)
        .filter(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end, Activity.type == "learning")
        .all()
    )
    learning_hours = round(sum(m or 0 for (m,) in learning_minutes) / 60, 1)

    projects_touched = (
        db.query(Activity.project_id)
        .join(Entry, Entry.id == Activity.entry_id)
        .filter(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end, Activity.project_id.is_not(None))
        .distinct()
        .count()
    )

    behavior = behavior_summary(db, user_id, start, end)

    this_week_topics = topic_interest_scores(db, user_id, start, end)
    top_focus = next(iter(this_week_topics), None)

    prev_week_topics = topic_interest_scores(db, user_id, prev_start, prev_end)
    emerging = None
    best_growth = 0.15  # minimum jump to bother calling something "emerging"
    for topic, score in this_week_topics.items():
        growth = score - prev_week_topics.get(topic, 0.0)
        if growth > best_growth:
            emerging, best_growth = topic, growth

    weekly_rows = weekly_behavior_deltas(db, user_id, now)
    improved = [r for r in weekly_rows if r["is_positive"] and r["change"] is not None]
    declined = [r for r in weekly_rows if r["is_positive"] is False and r["change"] is not None]

    biggest_improvement = None
    if improved:
        best = max(improved, key=lambda r: abs(r["change"]))
        biggest_improvement = {"label": best["label"], "change": best["change"]}

    watch = None
    if declined:
        worst = max(declined, key=lambda r: abs(r["change"]))
        watch = {"label": worst["label"], "change": worst["change"]}

    return WeeklyReview(
        period_start=start.date().isoformat(),
        period_end=(end - dt.timedelta(days=1)).date().isoformat(),
        entries_count=entries_count,
        learning_hours=learning_hours,
        projects_touched=projects_touched,
        completion_rate=behavior["completion_rate"],
        top_focus=top_focus,
        emerging_topic=emerging,
        biggest_improvement=biggest_improvement,
        watch=watch,
    )
