from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.rate_limit import RateLimitMiddleware


def _make_app():
    app = FastAPI()

    @app.post("/auth/login")
    def login():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"ok": True}

    app.add_middleware(RateLimitMiddleware, path_prefixes=("/auth/login",), max_requests=3, window_seconds=60)
    return app


def test_blocks_after_limit_on_matched_path():
    client = TestClient(_make_app())
    for _ in range(3):
        assert client.post("/auth/login").status_code == 200
    resp = client.post("/auth/login")
    assert resp.status_code == 429


def test_unmatched_path_is_never_limited():
    client = TestClient(_make_app())
    for _ in range(10):
        assert client.get("/health").status_code == 200
