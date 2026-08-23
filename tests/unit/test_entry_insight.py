import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.entry_insight import build_entry_insight
from src.database.base import Base
from src.database.models import Entry, EntryTopic, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _entry_with_topic(db, user_id, day: dt.date, topic: str) -> Entry:
    entry = Entry(user_id=user_id, raw_text=topic, entry_date=dt.datetime.combine(day, dt.time.min))
    db.add(entry)
    db.flush()
    db.add(EntryTopic(entry_id=entry.id, topic=topic))
    db.commit()
    db.refresh(entry)
    return entry


def test_recurring_topic_detected_within_week():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    today = dt.date(2026, 8, 23)
    _entry_with_topic(db, user.id, today - dt.timedelta(days=2), "RAG")
    _entry_with_topic(db, user.id, today - dt.timedelta(days=1), "RAG")
    todays_entry = _entry_with_topic(db, user.id, today, "RAG")

    insight = build_entry_insight(db, user.id, todays_entry)

    assert insight.recurring_topics
    assert insight.recurring_topics[0]["topic"] == "RAG"
    assert insight.recurring_topics[0]["mentions_this_week"] == 3
    assert insight.new_topics == []


def test_first_mention_is_a_new_topic():
    db = _make_session()
    user = User(email="c@d.com", hashed_password="x")
    db.add(user)
    db.flush()

    today = dt.date(2026, 8, 23)
    entry = _entry_with_topic(db, user.id, today, "LangGraph")

    insight = build_entry_insight(db, user.id, entry)

    assert insight.new_topics == ["LangGraph"]
    assert insight.recurring_topics == []


def test_insight_includes_streak_info():
    db = _make_session()
    user = User(email="e@f.com", hashed_password="x")
    db.add(user)
    db.flush()

    today = dt.date(2026, 8, 23)
    entry = _entry_with_topic(db, user.id, today, "Docker")

    insight = build_entry_insight(db, user.id, entry)

    assert insight.streak.current_streak == 1
    d = insight.to_dict()
    assert "streak" in d and "recurring_topics" in d and "new_topics" in d
