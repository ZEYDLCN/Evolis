import datetime as dt

from src.analytics.skill_graph import build_skill_graph
from src.database.base import Base
from src.database.models import Activity, Entry, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_skill_graph_only_includes_edges_present_in_user_data():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime.utcnow()
    for topic in ["Python", "Machine Learning"]:
        entry = Entry(user_id=user.id, raw_text=f"worked on {topic}", entry_date=now)
        db.add(entry)
        db.flush()
        db.add(Activity(entry_id=entry.id, type="learning", topic=topic, duration_minutes=60))
    db.commit()

    graph = build_skill_graph(db, user.id, now - dt.timedelta(days=30), now + dt.timedelta(days=1))

    skill_names = {n["skill"] for n in graph["nodes"]}
    assert {"Python", "Machine Learning"} <= skill_names
    assert {"from": "Python", "to": "Machine Learning"} in graph["edges"]
    # RAG was never mentioned, so no edge should reference it.
    assert all(e["to"] != "RAG" and e["from"] != "RAG" for e in graph["edges"])
