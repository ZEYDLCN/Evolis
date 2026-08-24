"""Regression test for a real bug hit in GitHub Codespaces testing: the
rate limiter was added as the OUTERMOST middleware (Starlette runs
middleware in reverse of add-order), so its 429 short-circuit response
never passed back through CORSMiddleware and came back with no
Access-Control-Allow-Origin header — the browser reported a confusing CORS
error instead of a legible 429. CORSMiddleware must be the outermost layer
so every response, short-circuited or not, gets the header.
"""
import importlib
import uuid


def _fresh_client(monkeypatch, origin: str):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", origin)
    monkeypatch.setenv("AUTH_RATE_LIMIT_MAX_REQUESTS", "1")
    monkeypatch.setenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")

    import apps.api.config as config
    import apps.api.main as main

    importlib.reload(config)
    importlib.reload(main)

    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    client.__enter__()  # runs lifespan (init_db) — closed by the caller not bothering, process-scoped test
    return client


def test_rate_limited_response_still_carries_cors_header(monkeypatch):
    origin = "https://example-codespace-3000.app.github.dev"
    client = _fresh_client(monkeypatch, origin)

    def register():
        return client.post(
            "/auth/register",
            json={"email": f"{uuid.uuid4()}@example.com", "password": "hunter2"},
            headers={"Origin": origin},
        )

    first = register()
    assert first.status_code == 201
    assert first.headers.get("access-control-allow-origin") == origin

    second = register()
    assert second.status_code == 429
    assert second.headers.get("access-control-allow-origin") == origin
