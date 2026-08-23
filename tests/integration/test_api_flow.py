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


def test_metrics_endpoint_reflects_traffic(client):
    client.get("/health")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "evolis_http_requests_total" in r.text
    assert 'path="/health"' in r.text


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

    r = client.get("/analytics/anomalies", headers=headers)
    assert r.status_code == 200

    r = client.get("/analytics/patterns", headers=headers)
    assert r.status_code == 200


def test_release_notes_endpoint(client):
    headers = _auth_headers(client)
    today = dt.date.today()

    client.post("/entries", json={"text": "LangGraph ile RAG pipeline geliştirdim."}, headers=headers)

    r = client.post(
        "/versions/generate",
        json={"period_start": (today - dt.timedelta(days=1)).isoformat(), "period_end": (today + dt.timedelta(days=1)).isoformat()},
        headers=headers,
    )
    label = r.json()["label"]

    r2 = client.post(
        "/versions/generate",
        json={"period_start": (today - dt.timedelta(days=1)).isoformat(), "period_end": (today + dt.timedelta(days=1)).isoformat()},
        headers=headers,
    )
    label2 = r2.json()["label"]

    r = client.get(f"/release-notes?base={label}&target={label2}", headers=headers)
    assert r.status_code == 200
    assert "text" in r.json()

    r = client.get(f"/release-notes/card?base={label}&target={label2}", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert r.text.startswith("<svg")


def test_knowledge_graph_endpoints(client):
    headers = _auth_headers(client)
    client.post("/entries", json={"text": "LangGraph ile RAG pipeline geliştirdim."}, headers=headers)

    r = client.get("/graph/export", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "nodes" in body and "relationships" in body

    r = client.post("/graph/sync", headers=headers)
    assert r.status_code == 200
    assert r.json()["synced"] is False  # NEO4J_URI not configured in tests


def test_account_export_and_delete(client):
    headers = _auth_headers(client)
    client.post("/entries", json={"text": "Docker ile uğraştım."}, headers=headers)

    r = client.get("/me/export", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["user"] is not None
    assert len(body["entries"]) == 1

    r = client.delete("/me", headers=headers)
    assert r.status_code == 204

    # The token now points at a deleted user.
    r = client.get("/entries", headers=headers)
    assert r.status_code == 401


def test_google_auth_reports_not_configured_by_default(client):
    r = client.get("/auth/google/config")
    assert r.status_code == 200
    assert r.json() == {"enabled": False, "client_id": None}

    r = client.post("/auth/google", json={"credential": "whatever"})
    assert r.status_code == 501


def test_google_auth_full_flow_when_configured(client, monkeypatch):
    monkeypatch.setattr("apps.api.config.GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")

    r = client.get("/auth/google/config")
    assert r.json() == {"enabled": True, "client_id": "test-client-id.apps.googleusercontent.com"}

    from src.services.google_auth import GoogleProfile

    monkeypatch.setattr(
        "apps.api.routers.auth.verify_google_credential",
        lambda credential: GoogleProfile(sub="sub-xyz", email="googleuser@example.com", name="G User"),
    )

    r = client.post("/auth/google", json={"credential": "fake-id-token"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/entries", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
