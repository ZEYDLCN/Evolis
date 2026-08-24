"""Goal system — sections 16-17.

Goals are plain to-dos by default (title + status). A goal can optionally
point at a real computed metric (metric_key/target_value) so progress is
measured against src/analytics data instead of a manually-ticked box.

Smart Goal Suggestions (section 17) are rule-based and deterministic —
built from the same analytics already computed elsewhere (interests,
behavior, streaks) — never LLM-guessed. Suggestions are never written to
the database on their own: the user must explicitly accept one (POST
/goals) before it becomes a real Goal row.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from src.analytics.interests import topic_interest_scores
from src.analytics.productivity import behavior_summary
from src.analytics.streaks import compute_streak
from src.database.models import Goal

WINDOW_DAYS = 30
DECLINE_THRESHOLD = 0.15  # topic score drop between the two halves of the window
COMPLETION_TARGET = 0.8
DEEP_WORK_TARGET_HOURS = 3.0
STREAK_TARGET_DAYS = 7


def create_goal(
    db: Session,
    user_id: str,
    title: str,
    description: str | None = None,
    metric_key: str | None = None,
    target_value: float | None = None,
    target_date: dt.date | None = None,
    source: str = "manual",
) -> Goal:
    goal = Goal(
        user_id=user_id,
        title=title,
        description=description,
        metric_key=metric_key,
        target_value=target_value,
        target_date=dt.datetime.combine(target_date, dt.time.min) if target_date else None,
        source=source,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def list_goals(db: Session, user_id: str) -> list[Goal]:
    return db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.created_at.desc()).all()


def complete_goal(db: Session, user_id: str, goal_id: str) -> Goal | None:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not goal:
        return None
    goal.status = "done"
    goal.completed_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, user_id: str, goal_id: str) -> bool:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not goal:
        return False
    db.delete(goal)
    db.commit()
    return True


def _goal_progress(db: Session, user_id: str, goal: Goal, now: dt.datetime) -> float | None:
    """Current value for a metric-backed goal, or None if not measurable."""
    if not goal.metric_key:
        return None
    start = now - dt.timedelta(days=WINDOW_DAYS)
    summary = behavior_summary(db, user_id, start, now)
    return summary.get(goal.metric_key)


def goals_with_progress(db: Session, user_id: str, now: dt.datetime | None = None) -> list[dict]:
    now = now or dt.datetime.utcnow()
    out = []
    for goal in list_goals(db, user_id):
        current_value = _goal_progress(db, user_id, goal, now)
        progress_pct = None
        if current_value is not None and goal.target_value:
            progress_pct = round(min(1.0, current_value / goal.target_value), 4) if goal.target_value else None
        out.append(
            {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "status": goal.status,
                "metric_key": goal.metric_key,
                "target_value": goal.target_value,
                "current_value": current_value,
                "progress_pct": progress_pct,
                "target_date": goal.target_date.date().isoformat() if goal.target_date else None,
                "source": goal.source,
                "created_at": goal.created_at.isoformat(),
                "completed_at": goal.completed_at.isoformat() if goal.completed_at else None,
            }
        )
    return out


def _gt(lang: str, en: str, tr: str) -> str:
    return tr if lang == "tr" else en


def suggest_goals(db: Session, user_id: str, now: dt.datetime | None = None, lang: str = "en") -> list[dict]:
    """Rule-based candidate goals. Pure read — nothing is persisted here."""
    now = now or dt.datetime.utcnow()
    window_start = now - dt.timedelta(days=WINDOW_DAYS)
    suggestions: list[dict] = []

    # 1. Completion rate below target.
    behavior = behavior_summary(db, user_id, window_start, now)
    if behavior["created"] >= 3 and behavior["completion_rate"] < COMPLETION_TARGET:
        suggestions.append(
            {
                "title": _gt(
                    lang,
                    f"Raise task completion rate to {int(COMPLETION_TARGET * 100)}%",
                    f"Görev tamamlanma oranını %{int(COMPLETION_TARGET * 100)}'e çıkar",
                ),
                "description": _gt(
                    lang,
                    f"You're at {round(behavior['completion_rate'] * 100)}% over the last {WINDOW_DAYS} days.",
                    f"Son {WINDOW_DAYS} günde %{round(behavior['completion_rate'] * 100)} durumundasın.",
                ),
                "metric_key": "completion_rate",
                "target_value": COMPLETION_TARGET,
                "reason": "completion_below_target",
            }
        )

    # 2. Deep work below target.
    if behavior["deep_work_hours_per_day"] < DEEP_WORK_TARGET_HOURS:
        suggestions.append(
            {
                "title": _gt(
                    lang,
                    f"Reach {DEEP_WORK_TARGET_HOURS:.0f}h of deep work per day",
                    f"Günde {DEEP_WORK_TARGET_HOURS:.0f} saat derin çalışmaya ulaş",
                ),
                "description": _gt(
                    lang,
                    f"Currently averaging {behavior['deep_work_hours_per_day']}h/day over the last {WINDOW_DAYS} days.",
                    f"Son {WINDOW_DAYS} günde günde ortalama {behavior['deep_work_hours_per_day']} saat.",
                ),
                "metric_key": "deep_work_hours_per_day",
                "target_value": DEEP_WORK_TARGET_HOURS,
                "reason": "deep_work_below_target",
            }
        )

    # 3. Streak below target.
    streak = compute_streak(db, user_id, today=now.date())
    if streak.current_streak < STREAK_TARGET_DAYS:
        suggestions.append(
            {
                "title": _gt(lang, f"Build a {STREAK_TARGET_DAYS}-day entry streak", f"{STREAK_TARGET_DAYS} günlük kayıt serisi oluştur"),
                "description": _gt(
                    lang, f"Current streak: {streak.current_streak} day(s).", f"Mevcut seri: {streak.current_streak} gün."
                ),
                "metric_key": None,
                "target_value": None,
                "reason": "streak_below_target",
            }
        )

    # 4. A declining topic: compare the two halves of the window.
    midpoint = window_start + dt.timedelta(days=WINDOW_DAYS // 2)
    early_scores = topic_interest_scores(db, user_id, window_start, midpoint)
    late_scores = topic_interest_scores(db, user_id, midpoint, now)
    for topic, early_score in early_scores.items():
        late_score = late_scores.get(topic, 0.0)
        if early_score - late_score >= DECLINE_THRESHOLD:
            suggestions.append(
                {
                    "title": _gt(lang, f"Re-engage with {topic}", f"{topic} ile yeniden ilgilen"),
                    "description": _gt(
                        lang,
                        f"{topic} interest dropped from {round(early_score * 100)}% to {round(late_score * 100)}% this month.",
                        f"{topic} ilgisi bu ay %{round(early_score * 100)}'den %{round(late_score * 100)}'e düştü.",
                    ),
                    "metric_key": None,
                    "target_value": None,
                    "reason": "declining_topic",
                }
            )
            break  # one at a time — don't overwhelm with every declining topic

    return suggestions
