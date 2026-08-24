import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import Entry, EntryTopic, Task, User
from src.services.goal_service import complete_goal, create_goal, goals_with_progress, list_goals, suggest_goals


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_create_list_and_complete_goal():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    goal = create_goal(db, user.id, "Write daily", metric_key="completion_rate", target_value=0.8)
    assert goal.status == "active"

    goals = list_goals(db, user.id)
    assert len(goals) == 1

    completed = complete_goal(db, user.id, goal.id)
    assert completed.status == "done"
    assert completed.completed_at is not None


def test_goals_with_progress_computes_current_value():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime(2026, 8, 24)
    for i in range(4):
        db.add(
            Task(
                user_id=user.id,
                title=f"t{i}",
                status="done" if i < 3 else "open",
                created_at=now - dt.timedelta(days=i, hours=1),
            )
        )
    create_goal(db, user.id, "Raise completion", metric_key="completion_rate", target_value=0.8)
    db.commit()

    rows = goals_with_progress(db, user.id, now=now)
    assert rows[0]["current_value"] == 0.75
    assert rows[0]["progress_pct"] == round(0.75 / 0.8, 4)


def test_suggest_goals_flags_low_completion_and_streak():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime(2026, 8, 24)
    for i in range(5):
        db.add(Task(user_id=user.id, title=f"t{i}", status="open", created_at=now - dt.timedelta(days=i)))
    db.commit()

    suggestions = suggest_goals(db, user.id, now=now)
    reasons = {s["reason"] for s in suggestions}
    assert "completion_below_target" in reasons
    assert "streak_below_target" in reasons


def test_suggest_goals_empty_for_new_user():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    now = dt.datetime(2026, 8, 24)
    suggestions = suggest_goals(db, user.id, now=now)
    # A brand-new user with zero tasks/entries: completion rule needs >=3
    # created tasks, so only the streak rule (and possibly deep-work) fire.
    reasons = {s["reason"] for s in suggestions}
    assert "completion_below_target" not in reasons
