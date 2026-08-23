import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import Activity, Entry, EntryTopic, Project, User
from src.graph.knowledge_graph import build_user_graph
from src.graph.neo4j_sync import neo4j_configured, sync_to_neo4j


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_build_user_graph_covers_all_relationship_types():
    db = _make_session()
    user = User(email="g@test.com", hashed_password="x")
    db.add(user)
    db.flush()

    project = Project(user_id=user.id, name="Voxera")
    db.add(project)
    db.flush()

    now = dt.datetime.utcnow()
    entry = Entry(user_id=user.id, raw_text="LangGraph ile Voxera backend geliştirdim.", entry_date=now)
    db.add(entry)
    db.flush()
    db.add(EntryTopic(entry_id=entry.id, topic="LangGraph"))
    db.add(Activity(entry_id=entry.id, type="project_development", topic="LangGraph", project_id=project.id, duration_minutes=60))
    db.commit()

    graph = build_user_graph(db, user.id, now - dt.timedelta(days=1), now + dt.timedelta(days=1))
    rel_types = {r.type for r in graph.relationships}
    node_labels = {n.label for n in graph.nodes}

    assert "LEARNS" in rel_types
    assert "BUILDS" in rel_types
    assert "USES" in rel_types
    assert "MENTIONS" in rel_types
    assert {"User", "Skill", "Project", "Entry", "Topic"} <= node_labels

    as_dict = graph.to_dict()
    assert "nodes" in as_dict and "relationships" in as_dict


def test_sync_to_neo4j_noop_without_config(monkeypatch):
    monkeypatch.delenv("NEO4J_URI", raising=False)
    db = _make_session()
    user = User(email="g2@test.com", hashed_password="x")
    db.add(user)
    db.commit()

    now = dt.datetime.utcnow()
    graph = build_user_graph(db, user.id, now - dt.timedelta(days=1), now + dt.timedelta(days=1))

    assert neo4j_configured() is False
    assert sync_to_neo4j(graph) is False


def test_sync_to_neo4j_noop_when_driver_not_installed(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    db = _make_session()
    user = User(email="g3@test.com", hashed_password="x")
    db.add(user)
    db.commit()

    now = dt.datetime.utcnow()
    graph = build_user_graph(db, user.id, now - dt.timedelta(days=1), now + dt.timedelta(days=1))

    # The neo4j driver isn't in requirements.txt's core deps and isn't
    # installed in this test environment, so this exercises the real
    # ImportError fallback path, not a mock.
    assert sync_to_neo4j(graph) is False
