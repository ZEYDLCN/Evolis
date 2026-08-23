import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.anomalies import detect_learning_time_anomalies
from src.analytics.patterns import detect_project_load_vs_completion
from src.database.base import Base
from src.database.models import Activity, Entry, Project, Task, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_learning_time_spike_is_flagged():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime.utcnow()
    monday_this_week = now - dt.timedelta(days=now.weekday())

    # 8 weeks of a quiet ~1h/week baseline.
    for i in range(1, 9):
        week_anchor = monday_this_week - dt.timedelta(weeks=i)
        entry = Entry(user_id=user.id, raw_text="normal week", entry_date=week_anchor)
        db.add(entry)
        db.flush()
        db.add(Activity(entry_id=entry.id, type="learning", topic="AI", duration_minutes=60))

    # This week: a huge spike.
    entry = Entry(user_id=user.id, raw_text="binge week", entry_date=monday_this_week)
    db.add(entry)
    db.flush()
    db.add(Activity(entry_id=entry.id, type="learning", topic="AI", duration_minutes=1200))
    db.commit()

    anomalies = detect_learning_time_anomalies(db, user.id, now=now)
    assert any(a.metric == "Total learning time" for a in anomalies)


def test_no_anomaly_when_flat():
    db = _make_session()
    user = User(email="c@d.com", hashed_password="x")
    db.add(user)
    db.flush()
    db.commit()

    anomalies = detect_learning_time_anomalies(db, user.id)
    assert anomalies == []


def test_project_load_pattern_needs_enough_weeks():
    db = _make_session()
    user = User(email="e@f.com", hashed_password="x")
    db.add(user)
    db.flush()
    db.commit()

    # No history at all -> nothing to report, not a crash.
    assert detect_project_load_vs_completion(db, user.id) is None
