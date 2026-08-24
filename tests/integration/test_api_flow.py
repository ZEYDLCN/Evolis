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


def test_entry_creation_returns_insight(client):
    headers = _auth_headers(client)

    r = client.post("/entries", json={"text": "Bugün LangGraph çalıştım."}, headers=headers)
    assert r.status_code == 201, r.text
    insight = r.json()["insight"]
    assert insight["streak"]["current"] == 1
    assert "LangGraph" in insight["new_topics"]


def test_streak_and_heatmap_and_onboarding_endpoints(client):
    headers = _auth_headers(client)

    r = client.get("/analytics/streak", headers=headers)
    assert r.status_code == 200
    assert r.json()["current_streak"] == 0

    r = client.get("/analytics/onboarding", headers=headers)
    assert r.status_code == 200
    assert r.json()["all_done"] is False

    client.post("/entries", json={"text": "RAG üzerine çalıştım."}, headers=headers)

    r = client.get("/analytics/streak", headers=headers)
    assert r.json()["current_streak"] == 1

    r = client.get("/analytics/heatmap?days=7", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 7
    assert sum(day["count"] for day in r.json()) == 1

    r = client.get("/analytics/onboarding", headers=headers)
    body = r.json()
    first_step = next(s for s in body["steps"] if s["key"] == "first_entry")
    assert first_step["done"] is True


def test_dashboard_summary_endpoint(client):
    headers = _auth_headers(client)

    r = client.get("/dashboard/summary", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["onboarding_gate"] is True

    client.post("/entries", json={"text": "RAG üzerine çalıştım."}, headers=headers)
    r = client.get("/dashboard/summary", headers=headers)
    assert r.status_code == 200
    assert "streak" in r.json() and "hero_headline" in r.json()


def test_evolis_score_and_weekly_review_endpoints(client):
    headers = _auth_headers(client)
    client.post("/entries", json={"text": "RAG üzerine çalıştım."}, headers=headers)

    r = client.get("/analytics/evolis-score", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"consistency", "focus", "execution", "learning"}

    r = client.get("/analytics/weekly-review", headers=headers)
    assert r.status_code == 200
    assert "entries_count" in r.json()


def test_search_endpoint_finds_entries_and_topics(client):
    headers = _auth_headers(client)
    client.post("/entries", json={"text": "LangGraph ile RAG pipeline geliştirdim."}, headers=headers)

    r = client.get("/search?q=LangGraph", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["entries"]) == 1
    assert "LangGraph" in body["topics"]


def test_day_detail_endpoint(client):
    headers = _auth_headers(client)
    client.post("/entries", json={"text": "RAG üzerine çalıştım."}, headers=headers)
    today = dt.date.today().isoformat()

    r = client.get(f"/day/{today}", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["entry_count"] == 1
    assert body["date"] == today

    r = client.get("/day/not-a-date", headers=headers)
    assert r.status_code == 422


def test_project_detail_endpoint(client):
    headers = _auth_headers(client)
    r = client.post("/projects", json={"name": "Voxera", "technologies": ["FastAPI"]}, headers=headers)
    project_id = r.json()["id"]

    r = client.get(f"/projects/{project_id}", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == project_id
    assert body["name"] == "Voxera"
    assert "focus_trend" in body and "timeline" in body

    r = client.get("/projects/does-not-exist", headers=headers)
    assert r.status_code == 404


def test_goals_crud_and_suggestions(client):
    headers = _auth_headers(client)

    r = client.get("/goals/suggestions", headers=headers)
    assert r.status_code == 200

    r = client.post("/goals", json={"title": "Ship v2"}, headers=headers)
    assert r.status_code == 201, r.text
    goal_id = r.json()["id"]

    r = client.get("/goals", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.post(f"/goals/{goal_id}/complete", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "done"

    r = client.delete(f"/goals/{goal_id}", headers=headers)
    assert r.status_code == 204

    r = client.delete(f"/goals/{goal_id}", headers=headers)
    assert r.status_code == 404


def test_entry_correction_records_feedback(client):
    headers = _auth_headers(client)
    r = client.post("/entries", json={"text": "LangGraph çalıştım."}, headers=headers)
    entry_id = r.json()["id"]

    r = client.patch(f"/entries/{entry_id}", json={"topics": ["LangGraph", "RAG"], "completion_status": "done"}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["completion_status"] == "done"
    assert set(r.json()["extraction"]["topics"]) == {"LangGraph", "RAG"}

    r = client.patch("/entries/does-not-exist", json={"completion_status": "done"}, headers=headers)
    assert r.status_code == 404


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
