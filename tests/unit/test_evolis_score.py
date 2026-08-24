import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.evolis_score import compute_evolis_score
from src.database.base import Base
from src.database.models import Activity, Entry, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_fresh_user_scores_at_or_near_zero():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    score = compute_evolis_score(db, user.id)
    assert score.consistency == 0
    assert score.execution == 0
    assert score.learning == 0


def test_high_activity_scores_high_but_capped_at_100():
    db = _make_session()
    user = User(email="c@d.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime(2026, 8, 23)
    for i in range(30):
        day = now - dt.timedelta(days=i)
        entry = Entry(user_id=user.id, raw_text="x", entry_date=day, completion_status="done")
        db.add(entry)
        db.flush()
        db.add(Activity(entry_id=entry.id, type="learning", topic="RAG", duration_minutes=240))
    db.commit()

    score = compute_evolis_score(db, user.id, now=now)
    assert score.consistency == 100
    assert score.execution == 100
    assert score.learning == 100
    assert 0 <= score.focus <= 100


def test_scores_never_exceed_bounds():
    db = _make_session()
    user = User(email="e@f.com", hashed_password="x")
    db.add(user)
    db.flush()
    now = dt.datetime(2026, 8, 23)
    for i in range(60):
        entry = Entry(user_id=user.id, raw_text="x", entry_date=now - dt.timedelta(days=i), completion_status="done")
        db.add(entry)
        db.flush()
        for _ in range(5):
            db.add(Activity(entry_id=entry.id, type="learning", duration_minutes=600))
    db.commit()

    score = compute_evolis_score(db, user.id, now=now)
    d = score.to_dict()
    assert all(0 <= v <= 100 for v in d.values())
