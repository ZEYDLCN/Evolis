import datetime as dt
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    # Reimport so the engine picks up the patched DATABASE_URL.
    import importlib

    import src.database.base as base_module

    importlib.reload(base_module)

    from apps.api.main import app

    with TestClient(app) as c:
        yield c


def _auth_headers(client: TestClient) -> dict:
    resp = client.post("/auth/register", json={"email": "user@example.com", "password": "hunter2"})
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
