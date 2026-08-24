import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.turning_points import detect_turning_point_candidates
from src.database.base import Base
from src.database.models import Entry, EntryTopic, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _log(db, user_id, day, topic):
    entry = Entry(user_id=user_id, raw_text=f"{topic} çalıştım.", entry_date=dt.datetime.combine(day, dt.time.min))
    db.add(entry)
    db.flush()
    db.add(EntryTopic(entry_id=entry.id, topic=topic))


def test_detects_a_clear_topic_shift():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime(2026, 8, 24)
    # 8 weeks of "Backend", then 8 weeks of "AI Engineering" — a sharp switch.
    for i in range(16, 8, -1):
        day = (now - dt.timedelta(weeks=i)).date()
        _log(db, user.id, day, "Backend")
    for i in range(8, 0, -1):
        day = (now - dt.timedelta(weeks=i)).date()
        _log(db, user.id, day, "AI Engineering")
    db.commit()

    candidates = detect_turning_point_candidates(db, user.id, now=now)
    assert len(candidates) >= 1
    top = candidates[0]
    assert top.shift_score > 0
    assert "AI Engineering" in top.new_topics or "AI Engineering" in top.metrics_after
    assert top.confidence in {"low", "medium", "high"}


def test_no_candidates_for_flat_activity():
    db = _make_session()
    user = User(email="c@d.com", hashed_password="x")
    db.add(user)
    db.flush()
    now = dt.datetime(2026, 8, 24)
    for i in range(16, 0, -1):
        day = (now - dt.timedelta(weeks=i)).date()
        _log(db, user.id, day, "Backend")
    db.commit()

    candidates = detect_turning_point_candidates(db, user.id, now=now)
    assert candidates == []


def test_no_candidates_for_no_data():
    db = _make_session()
    user = User(email="e@f.com", hashed_password="x")
    db.add(user)
    db.commit()

    candidates = detect_turning_point_candidates(db, user.id, now=dt.datetime(2026, 8, 24))
    assert candidates == []


def test_existing_dates_excludes_already_confirmed_weeks():
    db = _make_session()
    user = User(email="g@h.com", hashed_password="x")
    db.add(user)
    db.flush()
    now = dt.datetime(2026, 8, 24)
    for i in range(16, 8, -1):
        _log(db, user.id, (now - dt.timedelta(weeks=i)).date(), "Backend")
    for i in range(8, 0, -1):
        _log(db, user.id, (now - dt.timedelta(weeks=i)).date(), "AI Engineering")
    db.commit()

    all_candidates = detect_turning_point_candidates(db, user.id, now=now)
    assert all_candidates
    excluded = {all_candidates[0].week_start}
    filtered = detect_turning_point_candidates(db, user.id, now=now, existing_dates=excluded)
    assert all(c.week_start not in excluded for c in filtered)
