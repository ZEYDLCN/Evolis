from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import Entry, EntryTopic, Project, User
from src.services.search_service import search_all


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_search_finds_entries_projects_and_topics():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    entry = Entry(user_id=user.id, raw_text="Bugün LangGraph ile RAG pipeline geliştirdim.")
    db.add(entry)
    db.flush()
    db.add(EntryTopic(entry_id=entry.id, topic="LangGraph"))
    db.add(Project(user_id=user.id, name="LangGraph Agent"))
    db.commit()

    results = search_all(db, user.id, "LangGraph")
    assert len(results["entries"]) == 1
    assert "LangGraph" in results["entries"][0]["snippet"]
    assert any(p["name"] == "LangGraph Agent" for p in results["projects"])
    assert "LangGraph" in results["topics"]


def test_search_scopes_to_the_requesting_user():
    db = _make_session()
    user_a = User(email="a@b.com", hashed_password="x")
    user_b = User(email="c@d.com", hashed_password="x")
    db.add_all([user_a, user_b])
    db.flush()
    db.add(Entry(user_id=user_b.id, raw_text="Docker ile uğraştım."))
    db.commit()

    results = search_all(db, user_a.id, "Docker")
    assert results["entries"] == []


def test_empty_query_returns_empty_results():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    results = search_all(db, user.id, "   ")
    assert results == {"entries": [], "projects": [], "topics": [], "skills": [], "versions": []}
