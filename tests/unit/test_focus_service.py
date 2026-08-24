import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import User
from src.services.focus_service import list_focus_sessions, log_focus_session, todays_focus_minutes


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_log_and_list_focus_sessions():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    log_focus_session(db, user.id, 25)
    log_focus_session(db, user.id, 50, is_deep_work=False)

    sessions = list_focus_sessions(db, user.id)
    assert len(sessions) == 2


def test_todays_focus_minutes_sums_only_today():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    today = dt.date(2026, 8, 24)
    log_focus_session(db, user.id, 25, started_at=dt.datetime.combine(today, dt.time(9, 0)))
    log_focus_session(db, user.id, 25, started_at=dt.datetime.combine(today, dt.time(14, 0)))
    log_focus_session(db, user.id, 90, started_at=dt.datetime.combine(today - dt.timedelta(days=1), dt.time(9, 0)))

    assert todays_focus_minutes(db, user.id, today=today) == 50
