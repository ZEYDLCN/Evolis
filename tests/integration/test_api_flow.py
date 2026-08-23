import datetime as dt
import uuid

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _auth_headers(client: TestClient) -> dict:
    email = f"{uuid.uuid4()}@example.com"
    resp = client.post("/auth/register", json={"email": email, "password": "hunter2"})
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_flow(client):
    headers = _auth_headers(client)

    r = client.post(
        "/entries",
        json={"text": "Bugün 2 saat LangGraph çalıştım, RAG pipeline geliştirdim."},
        headers=headers,
    )
    assert r.status_code == 201, r.text

    r = client.get("/analytics/interests", headers=headers)
    assert r.status_code == 200
    assert "LangGraph" in r.json()

    r = client.get("/analytics/behavior", headers=headers)
    assert r.status_code == 200
    assert "completion_rate" in r.json()

    today = dt.date.today()
    r = client.post(
        "/versions/generate",
        json={"period_start": (today - dt.timedelta(days=1)).isoformat(), "period_end": (today + dt.timedelta(days=1)).isoformat()},
        headers=headers,
    )
    assert r.status_code == 201, r.text

    r = client.post("/ask", json={"question": "Son 6 ayda nasıl değiştim?"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["grounded"] is True


def test_entries_require_auth(client):
    r = client.get("/entries")
    assert r.status_code == 401


def test_tasks_drive_completion_rate(client):
    headers = _auth_headers(client)

    for title, complete in [("write tests", True), ("ship feature", True), ("refactor", False)]:
        r = client.post("/tasks", json={"title": title}, headers=headers)
        assert r.status_code == 201, r.text
        if complete:
            task_id = r.json()["id"]
            r2 = client.post(f"/tasks/{task_id}/complete", headers=headers)
            assert r2.status_code == 200

    r = client.get("/analytics/behavior", headers=headers)
    body = r.json()
    assert body["source"] == "tasks"
    assert body["created"] == 3
    assert body["completed"] == 2


def test_clusters_and_skill_graph_endpoints(client):
    headers = _auth_headers(client)

    texts = [
        "RAG retrieval çalıştım.",
        "Embedding modellerini karşılaştırdım.",
        "Vector search üzerine çalıştım.",
        "Docker container ayarladım.",
        "FastAPI endpoint yazdım.",
        "PostgreSQL sorgusu optimize ettim.",
    ]
    for text in texts:
        r = client.post("/entries", json={"text": text}, headers=headers)
        assert r.status_code == 201, r.text

    r = client.post("/clusters/rebuild", headers=headers)
    assert r.status_code == 200, r.text

    r = client.get("/clusters", headers=headers)
    assert r.status_code == 200

    r = client.get("/analytics/skill-graph", headers=headers)
    assert r.status_code == 200
    assert "nodes" in r.json() and "edges" in r.json()
