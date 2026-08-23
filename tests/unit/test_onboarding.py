import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.onboarding import compute_onboarding_status
from src.database.base import Base
from src.database.models import Entry, User, Version


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_fresh_user_has_nothing_done():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    status = compute_onboarding_status(db, user.id)
    assert status.all_done is False
    assert all(not s.done for s in status.steps)
    assert status.steps[0].progress == 0


def test_steps_unlock_progressively():
    db = _make_session()
    user = User(email="c@d.com", hashed_password="x")
    db.add(user)
    db.flush()

    base = dt.datetime(2026, 8, 1)
    for i in range(7):
        db.add(Entry(user_id=user.id, raw_text="x", entry_date=base + dt.timedelta(days=i)))
    db.add(Version(user_id=user.id, label="1.0", period_start=base, period_end=base + dt.timedelta(days=30)))
    db.commit()

    status = compute_onboarding_status(db, user.id)
    by_key = {s.key: s for s in status.steps}

    assert by_key["first_entry"].done is True
    assert by_key["three_entries"].done is True
    assert by_key["week_of_days"].done is True
    assert by_key["first_version"].done is True
    assert by_key["first_diff"].done is False  # only one version
    assert status.all_done is False


def test_all_done_once_two_versions_exist():
    db = _make_session()
    user = User(email="e@f.com", hashed_password="x")
    db.add(user)
    db.flush()

    base = dt.datetime(2026, 8, 1)
    for i in range(7):
        db.add(Entry(user_id=user.id, raw_text="x", entry_date=base + dt.timedelta(days=i)))
    for label in ["1.0", "1.1"]:
        db.add(Version(user_id=user.id, label=label, period_start=base, period_end=base + dt.timedelta(days=30)))
    db.commit()

    status = compute_onboarding_status(db, user.id)
    assert status.all_done is True
