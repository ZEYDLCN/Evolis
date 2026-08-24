import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.dashboard import build_dashboard_summary
from src.database.base import Base
from src.database.models import Activity, Entry, EntryTopic, User, Version


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _entry(db, user_id, day: dt.date, topic: str, duration=60):
    entry = Entry(user_id=user_id, raw_text=f"{topic} çalıştım.", entry_date=dt.datetime.combine(day, dt.time.min), completion_status="done")
    db.add(entry)
    db.flush()
    db.add(EntryTopic(entry_id=entry.id, topic=topic))
    db.add(Activity(entry_id=entry.id, type="learning", topic=topic, duration_minutes=duration))
    db.commit()
    return entry


def test_onboarding_gate_true_for_fresh_user():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    summary = build_dashboard_summary(db, user.id, display_name="Ada")

    assert summary.onboarding_gate is True
    assert summary.current_version is None
    assert summary.insight is None
    assert "Log a few more" in summary.hero_headline


def test_dashboard_summary_with_data():
    db = _make_session()
    user = User(email="c@d.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime(2026, 8, 23)
    for i in range(10):
        _entry(db, user.id, (now - dt.timedelta(days=i)).date(), "RAG")
    db.commit()

    summary = build_dashboard_summary(db, user.id, display_name="Ada", now=now)

    assert summary.onboarding_gate is False
    assert summary.focus_shift
    assert summary.focus_shift[0]["topic"] == "RAG"
    assert len(summary.recent_activity) == 5
    assert summary.recent_activity[0]["when"] == "Today"
    assert summary.streak["current"] == 10


def test_current_version_card_shows_growth_between_versions():
    db = _make_session()
    user = User(email="e@f.com", hashed_password="x")
    db.add(user)
    db.flush()

    base = dt.datetime(2026, 1, 1)
    v1 = Version(user_id=user.id, label="1.0", period_start=base, period_end=base + dt.timedelta(days=30))
    db.add(v1)
    db.flush()
    from src.database.models import VersionMetric

    db.add(VersionMetric(version_id=v1.id, key="topic_scores", value_json={"Frontend": 0.5}))
    db.add(VersionMetric(version_id=v1.id, key="completion_rate", value_number=0.5))

    v2 = Version(user_id=user.id, label="1.1", period_start=base + dt.timedelta(days=30), period_end=base + dt.timedelta(days=60))
    db.add(v2)
    db.flush()
    db.add(VersionMetric(version_id=v2.id, key="topic_scores", value_json={"Frontend": 0.2, "RAG": 0.6}))
    db.add(VersionMetric(version_id=v2.id, key="completion_rate", value_number=0.7))
    db.commit()

    summary = build_dashboard_summary(db, user.id, display_name=None, now=base + dt.timedelta(days=61))

    assert summary.current_version["label"] == "1.1"
    assert summary.current_version["strongest_growth"]["topic"] == "RAG"
    assert summary.current_version["has_previous_version"] is True


def test_turkish_lang_localizes_onboarding_headline():
    db = _make_session()
    user = User(email="tr@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    summary = build_dashboard_summary(db, user.id, display_name="Ada", lang="tr")

    assert summary.onboarding_gate is True
    assert "Birkaç gün daha" in summary.hero_headline


def test_turkish_lang_localizes_weekly_evolution_labels():
    db = _make_session()
    user = User(email="tr2@b.com", hashed_password="x")
    db.add(user)
    db.flush()
    for i in range(3):
        _entry(db, user.id, dt.date(2026, 8, 20) + dt.timedelta(days=i), "RAG")

    summary = build_dashboard_summary(db, user.id, display_name=None, now=dt.datetime(2026, 8, 24), lang="tr")

    labels = {row["label"] for row in summary.weekly_evolution}
    assert "Derin Çalışma" in labels
    assert "Tamamlanma" in labels
    assert "Bağlam Değişimi" in labels
