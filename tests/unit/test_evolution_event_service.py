import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import Entry, EntryTopic, EvolutionEvent, User
from src.services.evolution_event_service import (
    create_event,
    decision_impact,
    delete_event,
    list_events,
    rank_decisions_by_impact,
    serialize_event,
)


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _log(db, user_id, day, topic):
    entry = Entry(user_id=user_id, raw_text=f"{topic} çalıştım.", entry_date=dt.datetime.combine(day, dt.time.min))
    db.add(entry)
    db.flush()
    db.add(EntryTopic(entry_id=entry.id, topic=topic))


def test_create_list_and_delete_event():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    event = create_event(db, user.id, "decision", "Focus on AI Engineering", dt.date(2026, 5, 14))
    assert event.type == "decision"

    events = list_events(db, user.id)
    assert len(events) == 1
    assert serialize_event(events[0])["title"] == "Focus on AI Engineering"

    assert delete_event(db, user.id, event.id) is True
    assert list_events(db, user.id) == []


def test_decision_impact_shows_observed_changes_not_causal_claims():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    decision_date = dt.date(2026, 5, 14)
    for i in range(6, 0, -1):
        _log(db, user.id, decision_date - dt.timedelta(weeks=i), "Backend")
    for i in range(0, 6):
        _log(db, user.id, decision_date + dt.timedelta(weeks=i), "AI Engineering")
    db.commit()

    event = create_event(db, user.id, "decision", "Focus on AI Engineering", decision_date)
    now = dt.datetime.combine(decision_date, dt.time.min) + dt.timedelta(weeks=8)
    impact = decision_impact(db, user.id, event, now=now)

    assert impact["has_enough_after_data"] is True
    assert any(c["topic"] == "AI Engineering" and c["change"] > 0 for c in impact["topic_changes"])
    assert "AI Engineering" in impact["new_topics"]
    assert "Backend" in impact["faded_topics"]


def test_decision_impact_flags_insufficient_after_data():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()
    decision_date = dt.date(2026, 8, 20)
    db.commit()

    event = create_event(db, user.id, "decision", "Just decided", decision_date)
    now = dt.datetime.combine(decision_date, dt.time.min) + dt.timedelta(days=2)
    impact = decision_impact(db, user.id, event, now=now)
    assert impact["has_enough_after_data"] is False


def test_rank_decisions_by_impact_orders_by_magnitude():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    decision_date = dt.date(2026, 5, 14)
    for i in range(6, 0, -1):
        _log(db, user.id, decision_date - dt.timedelta(weeks=i), "Backend")
    for i in range(0, 6):
        _log(db, user.id, decision_date + dt.timedelta(weeks=i), "AI Engineering")
    db.commit()

    create_event(db, user.id, "decision", "Big shift", decision_date)
    create_event(db, user.id, "decision", "Minor note", dt.date(2026, 1, 1))

    now = dt.datetime.combine(decision_date, dt.time.min) + dt.timedelta(weeks=8)
    ranked = rank_decisions_by_impact(db, user.id, now=now)
    assert ranked
    assert ranked[0]["event"]["title"] == "Big shift"
