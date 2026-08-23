import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.graph import run_ask_graph
from src.database.base import Base
from src.database.models import Activity, Entry, User


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_ask_graph_runs_all_stages_and_grounds_the_answer():
    db = _make_session()
    user = User(email="graph@test.com", hashed_password="x")
    db.add(user)
    db.flush()

    now = dt.datetime.utcnow()
    entry = Entry(user_id=user.id, raw_text="RAG üzerine çalıştım.", entry_date=now, completion_status="done")
    db.add(entry)
    db.flush()
    db.add(Activity(entry_id=entry.id, type="learning", topic="RAG", duration_minutes=60))
    db.commit()

    result = run_ask_graph(db, user.id, "Hangi konulara ilgim arttı?")

    assert result["question"] == "Hangi konulara ilgim arttı?"
    assert result["query_class"] == "interest_change"
    assert result["grounded"] is True
    assert "analysis" in result and "answer" in result


def test_ask_graph_handles_no_data_without_crashing():
    db = _make_session()
    user = User(email="empty@test.com", hashed_password="x")
    db.add(user)
    db.commit()

    result = run_ask_graph(db, user.id, "Hangi konulara ilgim arttı?")
    assert result["grounded"] is True
    assert isinstance(result["answer"], str)
