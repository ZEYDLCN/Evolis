import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import (
    account,
    analytics,
    ask,
    auth,
    clusters,
    dashboard,
    day,
    diff,
    entries,
    evolution_events,
    focus,
    goals,
    graph,
    notifications,
    projects,
    search,
    tasks,
    timeline,
    versions,
)
from apps.api.config import (
    AUTH_RATE_LIMIT_MAX_REQUESTS,
    AUTH_RATE_LIMIT_WINDOW_SECONDS,
    CORS_ALLOWED_ORIGINS,
    CORS_EXPLICITLY_SET,
    ENVIRONMENT,
    SECRET_KEY,
)
from apps.api.rate_limit import RateLimitMiddleware
from src.database.base import init_db
from src.monitoring.metrics import http_request_duration_seconds, http_requests_total, render_metrics


def _check_production_config() -> None:
    """Refuse to boot with dev defaults in production rather than serving
    a JWT signed with a publicly-known key, or a wide-open CORS policy."""
    if ENVIRONMENT != "production":
        return
    if SECRET_KEY == "dev-secret-change-me":
        raise RuntimeError("SECRET_KEY must be set to a real secret when ENVIRONMENT=production")
    if not CORS_EXPLICITLY_SET or "*" in CORS_ALLOWED_ORIGINS:
        raise RuntimeError("CORS_ALLOWED_ORIGINS must be set explicitly (no wildcard) when ENVIRONMENT=production")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_production_config()
    init_db()
    yield


app = FastAPI(
    title="Evolis API",
    description="Version control for your life — AI-powered personal evolution analytics.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cheap brute-force guard on auth endpoints. In-memory, so it resets on
# restart and doesn't share state across multiple API replicas — fine for a
# single-instance deployment; swap for a Redis-backed limiter (REDIS_URL is
# already provisioned for Celery) before running more than one replica.
if AUTH_RATE_LIMIT_MAX_REQUESTS > 0:
    app.add_middleware(
        RateLimitMiddleware,
        path_prefixes=("/auth/login", "/auth/register"),
        max_requests=AUTH_RATE_LIMIT_MAX_REQUESTS,
        window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
    )


@app.middleware("http")
async def _prometheus_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)

    # Prefer the matched route template (e.g. "/projects/{project_id}/dashboard")
    # over the raw path, so per-id URLs don't each get their own label series.
    route = request.scope.get("route")
    path = route.path if route else request.url.path

    http_requests_total.labels(method=request.method, path=path, status_code=response.status_code).inc()
    http_request_duration_seconds.labels(method=request.method, path=path).observe(time.perf_counter() - start)
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


app.include_router(auth.router)
app.include_router(entries.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(clusters.router)
app.include_router(account.router)
app.include_router(graph.router)
app.include_router(dashboard.router)
app.include_router(timeline.router)
app.include_router(analytics.router)
app.include_router(versions.router)
app.include_router(diff.router)
app.include_router(ask.router)
app.include_router(search.router)
app.include_router(goals.router)
app.include_router(day.router)
app.include_router(focus.router)
app.include_router(notifications.router)
app.include_router(evolution_events.router)
