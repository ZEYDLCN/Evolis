"""Evolution Events — CRUD + decision-impact analysis for Turning Points
and Decisions ("Evolution Forks").

A decision's "impact" is never framed as causal: it's the same before/
after comparison the Diff engine already does (src/versions/diff.py),
just anchored to an event date instead of two version snapshots. The
wording throughout is "observed changes after this decision," never
"this decision caused."
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from src.analytics.interests import topic_interest_scores
from src.analytics.productivity import behavior_summary
from src.database.models import EvolutionEvent

IMPACT_WINDOW_WEEKS = 6


def create_event(
    db: Session,
    user_id: str,
    type: str,
    title: str,
    event_date: dt.date,
    description: str | None = None,
    source: str = "manual",
    entry_id: str | None = None,
    metadata: dict | None = None,
) -> EvolutionEvent:
    event = EvolutionEvent(
        user_id=user_id,
        type=type,
        title=title,
        description=description,
        event_date=dt.datetime.combine(event_date, dt.time.min),
        source=source,
        entry_id=entry_id,
        metadata_json=metadata,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, user_id: str) -> list[EvolutionEvent]:
    return db.query(EvolutionEvent).filter(EvolutionEvent.user_id == user_id).order_by(EvolutionEvent.event_date.desc()).all()


def get_event(db: Session, user_id: str, event_id: str) -> EvolutionEvent | None:
    return db.query(EvolutionEvent).filter(EvolutionEvent.id == event_id, EvolutionEvent.user_id == user_id).first()


def delete_event(db: Session, user_id: str, event_id: str) -> bool:
    event = get_event(db, user_id, event_id)
    if not event:
        return False
    db.delete(event)
    db.commit()
    return True


def serialize_event(event: EvolutionEvent) -> dict:
    return {
        "id": event.id,
        "type": event.type,
        "title": event.title,
        "description": event.description,
        "event_date": event.event_date.date().isoformat(),
        "source": event.source,
        "entry_id": event.entry_id,
        "metadata": event.metadata_json,
        "created_at": event.created_at.isoformat(),
    }


def decision_impact(db: Session, user_id: str, event: EvolutionEvent, now: dt.datetime | None = None) -> dict:
    """Before/after topic interest + behavior around an event date, capped
    at `now` on the "after" side so a decision logged last week doesn't
    pretend to have 6 weeks of hindsight it doesn't have yet."""
    now = now or dt.datetime.utcnow()
    event_dt = event.event_date if isinstance(event.event_date, dt.datetime) else dt.datetime.combine(event.event_date, dt.time.min)
    window = dt.timedelta(weeks=IMPACT_WINDOW_WEEKS)

    before_start = event_dt - window
    after_end = min(event_dt + window, now)

    before_topics = topic_interest_scores(db, user_id, before_start, event_dt)
    after_topics = topic_interest_scores(db, user_id, event_dt, after_end)
    before_behavior = behavior_summary(db, user_id, before_start, event_dt)
    after_behavior = behavior_summary(db, user_id, event_dt, after_end)

    all_topics = set(before_topics) | set(after_topics)
    changes = []
    for topic in all_topics:
        before_score = before_topics.get(topic, 0.0)
        after_score = after_topics.get(topic, 0.0)
        delta = after_score - before_score
        if abs(delta) < 0.1:
            continue
        changes.append({"topic": topic, "before": round(before_score, 4), "after": round(after_score, 4), "change": round(delta, 4)})
    changes.sort(key=lambda c: abs(c["change"]), reverse=True)

    new_topics = sorted((t for t in after_topics if after_topics[t] >= 0.15 and before_topics.get(t, 0.0) < 0.15), key=lambda t: -after_topics[t])
    faded_topics = sorted((t for t in before_topics if before_topics[t] >= 0.15 and after_topics.get(t, 0.0) < 0.15), key=lambda t: -before_topics[t])

    days_since = (now - event_dt).days
    return {
        "event": serialize_event(event),
        "has_enough_after_data": days_since >= 7,
        "topics_before": before_topics,
        "topics_after": after_topics,
        "behavior_before": before_behavior,
        "behavior_after": after_behavior,
        "topic_changes": changes[:8],
        "new_topics": new_topics[:3],
        "faded_topics": faded_topics[:3],
    }


def _impact_magnitude(impact: dict) -> float:
    """A single comparable number for ranking decisions by how much
    coincided with them — sum of |topic score changes| plus a scaled
    completion-rate delta. Purely for sorting, never shown as "caused by."""
    topic_component = sum(abs(c["change"]) for c in impact["topic_changes"])
    completion_before = impact["behavior_before"].get("completion_rate", 0.0)
    completion_after = impact["behavior_after"].get("completion_rate", 0.0)
    return topic_component + abs(completion_after - completion_before)


def rank_decisions_by_impact(db: Session, user_id: str, now: dt.datetime | None = None, limit: int = 3) -> list[dict]:
    now = now or dt.datetime.utcnow()
    decisions = [e for e in list_events(db, user_id) if e.type == "decision"]
    ranked = []
    for decision in decisions:
        impact = decision_impact(db, user_id, decision, now)
        if not impact["has_enough_after_data"]:
            continue
        magnitude = _impact_magnitude(impact)
        if magnitude <= 0:
            continue
        ranked.append({"event": serialize_event(decision), "magnitude": round(magnitude, 4), "top_change": impact["topic_changes"][0] if impact["topic_changes"] else None})
    ranked.sort(key=lambda r: r["magnitude"], reverse=True)
    return ranked[:limit]
