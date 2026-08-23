from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import analytics, ask, auth, diff, entries, projects, timeline, versions
from src.database.base import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="LifeDiff API",
    description="Version control for your life — AI-powered personal evolution analytics.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(entries.router)
app.include_router(projects.router)
app.include_router(timeline.router)
app.include_router(analytics.router)
app.include_router(versions.router)
app.include_router(diff.router)
app.include_router(ask.router)
