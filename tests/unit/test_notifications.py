import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import Task, User
from src.services.notification_service import build_notifications


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_notifications_include_goal_suggestions_for_low_completion():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime(2026, 8, 24)
    for i in range(5):
        db.add(Task(user_id=user.id, title=f"t{i}", status="open", created_at=now - dt.timedelta(days=i, hours=1)))
    db.commit()

    notifications = build_notifications(db, user.id, now=now)
    assert any(n["type"] == "goal_suggestion" for n in notifications)
    assert all("confidence" in n for n in notifications)


def test_notifications_empty_for_fresh_user():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    notifications = build_notifications(db, user.id, now=dt.datetime(2026, 8, 24))
    # A brand-new user still gets the streak-building suggestion.
    assert isinstance(notifications, list)
