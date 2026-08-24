import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.weekly_review import build_weekly_review
from src.database.base import Base
from src.database.models import Activity, Entry, EntryTopic, Project, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_empty_week_has_zeroed_review():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    review = build_weekly_review(db, user.id, now=dt.datetime(2026, 8, 23))
    assert review.entries_count == 0
    assert review.learning_hours == 0
    assert review.top_focus is None


def test_week_with_activity():
    db = _make_session()
    user = User(email="c@d.com", hashed_password="x")
    db.add(user)
    db.flush()

    project = Project(user_id=user.id, name="Voxera")
    db.add(project)
    db.flush()

    now = dt.datetime(2026, 8, 23)  # a Sunday
    monday = now - dt.timedelta(days=now.weekday())
    for i in range(3):
        entry = Entry(user_id=user.id, raw_text="RAG çalıştım.", entry_date=monday + dt.timedelta(days=i), completion_status="done")
        db.add(entry)
        db.flush()
        db.add(EntryTopic(entry_id=entry.id, topic="RAG"))
        db.add(Activity(entry_id=entry.id, type="learning", topic="RAG", project_id=project.id, duration_minutes=120))
    db.commit()

    review = build_weekly_review(db, user.id, now=now)
    assert review.entries_count == 3
    assert review.learning_hours == 6.0
    assert review.projects_touched == 1
    assert review.top_focus == "RAG"
    assert review.completion_rate == 1.0
    d = review.to_dict()
    assert "period_start" in d and "period_end" in d
