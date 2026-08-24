import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.domains import domain_breakdown
from src.database.base import Base
from src.database.models import Entry, EntryTopic, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_domain_breakdown_groups_topics_by_life_domain():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime.utcnow()
    for topic in ["English", "Walking", "Reading", "Voxera", "Low Focus"]:
        entry = Entry(user_id=user.id, raw_text=topic, entry_date=now)
        db.add(entry)
        db.flush()
        db.add(EntryTopic(entry_id=entry.id, topic=topic))
    db.commit()

    breakdown = domain_breakdown(db, user.id, now - dt.timedelta(days=7), now + dt.timedelta(days=1))

    assert "English" in breakdown["Learning"]
    assert "Walking" in breakdown["Habits & Routines"]
    assert "Reading" in breakdown["Personal Growth"]
    assert "Voxera" in breakdown["Skills"]
    assert "Low Focus" in breakdown["Behavior"]


def test_domain_breakdown_empty_for_no_activity():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    now = dt.datetime.utcnow()
    assert domain_breakdown(db, user.id, now - dt.timedelta(days=7), now) == {}
