import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.day_detail import build_day_detail
from src.database.base import Base
from src.database.models import Activity, Entry, EntryTopic, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_day_with_no_entries_is_empty():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    detail = build_day_detail(db, user.id, dt.date(2026, 8, 24))
    assert detail["entry_count"] == 0
    assert detail["focused_minutes"] == 0
    assert detail["entries"] == []


def test_day_aggregates_entries_and_topic_breakdown():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    day = dt.date(2026, 8, 24)
    entry = Entry(user_id=user.id, raw_text="LangGraph çalıştım.", entry_date=dt.datetime.combine(day, dt.time(10, 0)))
    db.add(entry)
    db.flush()
    db.add(EntryTopic(entry_id=entry.id, topic="LangGraph"))
    db.add(Activity(entry_id=entry.id, type="learning", topic="LangGraph", duration_minutes=90))
    db.commit()

    detail = build_day_detail(db, user.id, day)
    assert detail["entry_count"] == 1
    assert detail["focused_minutes"] == 90
    assert detail["topic_breakdown"] == {"LangGraph": 90}
    assert detail["entries"][0]["topics"] == ["LangGraph"]
