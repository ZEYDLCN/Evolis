import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.trend_forecast import forecast_completion_rate, forecast_deep_work
from src.database.base import Base
from src.database.models import Task, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_forecast_flat_for_new_user():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    forecast = forecast_completion_rate(db, user.id, now=dt.datetime(2026, 8, 24))
    assert forecast.direction == "flat"
    assert forecast.forecast_next == 0.0
    assert len(forecast.history) == 8


def test_forecast_detects_upward_completion_trend():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime(2026, 8, 24)  # a Monday — anchor for week offset 0 falls on a week boundary
    # Each week further back has a lower completion rate -> rising trend.
    for week in range(8):
        # Middle of the target week, so it never spills into the adjacent
        # Mon-Sun bucket regardless of which weekday `now` happens to be.
        anchor = now - dt.timedelta(weeks=week) + dt.timedelta(days=2)
        done_count = 8 - week  # more done tasks in recent weeks
        for i in range(done_count):
            db.add(Task(user_id=user.id, title=f"t{week}-{i}", status="done", created_at=anchor))
        for i in range(2):
            db.add(Task(user_id=user.id, title=f"o{week}-{i}", status="open", created_at=anchor))
    db.commit()

    forecast = forecast_completion_rate(db, user.id, now=now)
    assert forecast.direction == "up"
    assert 0.0 <= forecast.forecast_next <= 1.0
    assert forecast.confidence in {"low", "medium", "high"}


def test_deep_work_forecast_shape():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    forecast = forecast_deep_work(db, user.id, now=dt.datetime(2026, 8, 24))
    assert forecast.metric == "deep_work_hours_per_day"
    assert forecast.forecast_next >= 0
