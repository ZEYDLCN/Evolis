import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.streaks import compute_heatmap, compute_streak
from src.database.base import Base
from src.database.models import Entry, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _add_entry(db, user_id, day: dt.date):
    db.add(Entry(user_id=user_id, raw_text="x", entry_date=dt.datetime.combine(day, dt.time.min)))


def test_no_entries_has_zero_streak():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    streak = compute_streak(db, user.id)
    assert streak.current_streak == 0
    assert streak.longest_streak == 0
    assert streak.last_entry_date is None


def test_consecutive_days_including_today():
    db = _make_session()
    user = User(email="c@d.com", hashed_password="x")
    db.add(user)
    db.flush()

    today = dt.date(2026, 8, 23)
    for offset in range(5):  # today, yesterday, ... 4 days ago
        _add_entry(db, user.id, today - dt.timedelta(days=offset))
    db.commit()

    streak = compute_streak(db, user.id, today=today)
    assert streak.current_streak == 5
    assert streak.longest_streak == 5
    assert streak.is_new_best is True


def test_streak_still_counts_yesterday_if_today_not_logged_yet():
    db = _make_session()
    user = User(email="e@f.com", hashed_password="x")
    db.add(user)
    db.flush()

    today = dt.date(2026, 8, 23)
    _add_entry(db, user.id, today - dt.timedelta(days=1))
    _add_entry(db, user.id, today - dt.timedelta(days=2))
    db.commit()

    streak = compute_streak(db, user.id, today=today)
    assert streak.current_streak == 2  # not logging today yet doesn't zero it out


def test_gap_breaks_streak_and_longest_is_remembered():
    db = _make_session()
    user = User(email="g@h.com", hashed_password="x")
    db.add(user)
    db.flush()

    today = dt.date(2026, 8, 23)
    # A 4-day streak two weeks ago, then a 1-day gap, then today only.
    for offset in [16, 15, 14, 13]:
        _add_entry(db, user.id, today - dt.timedelta(days=offset))
    _add_entry(db, user.id, today)
    db.commit()

    streak = compute_streak(db, user.id, today=today)
    assert streak.current_streak == 1
    assert streak.longest_streak == 4
    assert streak.is_new_best is False


def test_heatmap_is_zero_filled_and_counts_multiple_entries_per_day():
    db = _make_session()
    user = User(email="i@j.com", hashed_password="x")
    db.add(user)
    db.flush()

    today = dt.date(2026, 8, 23)
    _add_entry(db, user.id, today)
    _add_entry(db, user.id, today)  # two entries same day
    db.commit()

    heatmap = compute_heatmap(db, user.id, days=3, today=today)
    assert len(heatmap) == 3
    by_date = {row["date"]: row["count"] for row in heatmap}
    assert by_date[today.isoformat()] == 2
    assert by_date[(today - dt.timedelta(days=1)).isoformat()] == 0
