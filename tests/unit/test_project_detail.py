import datetime as dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import Activity, Entry, Project, User
from src.services.project_service import project_detail


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_project_detail_aggregates_sessions_and_timeline():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()
    project = Project(user_id=user.id, name="Voxera", technologies=["FastAPI"])
    db.add(project)
    db.flush()

    for i in range(3):
        entry = Entry(user_id=user.id, raw_text=f"Voxera üzerine çalıştım {i}", entry_date=dt.datetime(2026, 8, 1 + i))
        db.add(entry)
        db.flush()
        db.add(Activity(entry_id=entry.id, type="project_development", topic="FastAPI", project_id=project.id, duration_minutes=60))
    db.commit()

    detail = project_detail(db, user.id, project.id)
    assert detail["name"] == "Voxera"
    assert detail["active_days"] == 3
    assert detail["total_sessions"] == 3
    assert detail["estimated_focus_hours"] == 3.0
    assert "FastAPI" in detail["topics_touched"]
    assert len(detail["timeline"]) == 3


def test_project_detail_raises_for_missing_or_other_users_project():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    other = User(email="c@d.com", hashed_password="x")
    db.add_all([user, other])
    db.flush()
    project = Project(user_id=other.id, name="Not yours")
    db.add(project)
    db.commit()

    with pytest.raises(ValueError):
        project_detail(db, user.id, project.id)
