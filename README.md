# LifeDiff

> **Version Control for Your Life**
> LifeDiff turns your daily activity into a version history of yourself.

LifeDiff is an AI-powered personal evolution analytics platform. You write a
short natural-language entry about your day; it extracts structured
activity, tracks your interests and skills over time, and shows how you
change — as a version diff, not a habit-tracker streak.

```
YOU v1.4 → YOU v1.7

Added
+ RAG
+ LangGraph

Improved
↑ Deep Work +34%
↑ Completion Rate +16%

Declining
- Frontend

Emerging Interest
→ Agentic AI
```

Full product spec + architecture decisions: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Quickstart

```bash
cp .env.example .env
pip install -r requirements.txt
alembic upgrade head        # or skip it — the API also self-creates tables on startup for dev
uvicorn apps.api.main:app --reload
```

Open `http://localhost:8000/docs` for the interactive API.

The app runs with zero external services out of the box: SQLite for storage,
a regex-based extractor, and a hashing-based embedding — see
[docs/ARCHITECTURE.md § Degradation strategy](docs/ARCHITECTURE.md#5-degradation-strategy)
for what upgrades when you add `ANTHROPIC_API_KEY`, Postgres+pgvector, or the
optional ML dependencies.

### Full stack (Postgres + pgvector, Redis, worker, frontend)

```bash
docker compose up --build
```

### Try it

```bash
# Register + capture the token
TOKEN=$(curl -s -X POST localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"hunter2"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# Log a day
curl -s -X POST localhost:8000/entries \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"text":"Bugün 2 saat LangGraph çalıştım, RAG pipeline geliştirdim."}'

# See what it extracted into
curl -s localhost:8000/analytics/interests -H "Authorization: Bearer $TOKEN"

# Ask it a question
curl -s -X POST localhost:8000/ask -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"question":"Son 6 ayda nasıl değiştim?"}'
```

## Tests

```bash
python3 -m pytest tests/ -q
```

## Project structure

```
apps/api/       FastAPI app (routers, auth dependency, config)
apps/worker/    Celery background jobs (embeddings, cluster rebuild, version snapshots)
apps/frontend/  Next.js scaffold (screens: Today, Timeline, Diff, Profile, Projects, Insights, Ask)
src/            All the actual logic — extraction, embeddings, ML scoring, analytics, versions/diff, RAG, agents
tests/          Unit tests (pure logic) + integration tests (full API flow)
docs/           Architecture + product notes
docker/         Dockerfiles for api/worker; see docker-compose.yml at the root
```

## Status

MVP+: daily entry ingestion, structured extraction, interest/skill scoring,
version snapshots, the diff engine, timeline, task-based completion
tracking, semantic clustering with LLM-named topics, a skill progression
graph, anomaly and pattern detection, shareable release notes, self-service
data export/account deletion, a Next.js frontend wired to all of it, and a
rule-based Ask LifeDiff pipeline (classify → plan → SQL/vector analysis →
grounded answer). Schema is managed with Alembic (`alembic upgrade head`). See
[docs/ARCHITECTURE.md § What's intentionally NOT built yet](docs/ARCHITECTURE.md#8-whats-intentionally-not-built-yet-phase-2--3-per-original-spec)
for what's still open (LangGraph orchestration, monitoring stack, Knowledge
Graph, etc).

### Frontend

```bash
cd apps/frontend
npm install
npm run dev   # http://localhost:3000, expects the API at NEXT_PUBLIC_API_URL (default localhost:8000)
```

Screens: Login/Register, Today (daily check-in), Timeline, Diff, Profile
(version generation), Projects, Insights (interests/skills/skill graph/
behavior), Ask LifeDiff. Auth token lives in `localStorage`; no state
library — plain `fetch` calls through `apps/frontend/lib/api.ts`.
