# Evolis

> **Personal Evolution Intelligence**
> Evolis turns your daily activity into a version history of yourself.

Brand assets live in `apps/frontend/public/brand/` (icon, monochrome icon,
horizontal wordmark). Palette: Deep Forest `#0B2A1E`, Emerald `#168B62`,
Mid Green `#4AAE70`, Lime Accent `#C7F36A` — see
`apps/frontend/lib/styles.ts` for the tokens the whole frontend is built on.

Evolis is an AI-powered personal evolution analytics platform. You write a
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

Includes an extraction/retrieval evaluation harness against a golden
dataset (`tests/evaluation/`) — a regression guard for the extraction
pipeline's accuracy, not just its plumbing. CI (`.github/workflows/ci.yml`)
runs this plus `alembic check` (schema drift) and a frontend `next build`
on every push/PR to `main`.

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

Feature-complete against the spec's MVP + Phase 2/3 architecture, short of
the pieces that need a real external account or a production target no one
has set up yet (mobile app, calendar/git OAuth integrations, an actual
deployment). Everything else is implemented and tested: daily entry
ingestion, structured extraction, interest/skill scoring, version
snapshots, the diff engine, timeline, task-based completion tracking,
semantic clustering with LLM-named topics (+ silhouette/stability quality
metrics), a skill progression graph, anomaly and pattern detection,
shareable release notes (text + downloadable SVG card), a computed
Knowledge Graph export (optional Neo4j sync), opt-in encryption at rest,
self-service data export/account deletion, Prometheus metrics, a Next.js
frontend wired to all of it, and Ask Evolis running as a real LangGraph
`StateGraph` (classify → plan → SQL/vector analysis → explain → verify →
grounded answer). Schema is managed with Alembic (`alembic upgrade head`).
See [docs/ARCHITECTURE.md § What's intentionally NOT built yet](docs/ARCHITECTURE.md#8-whats-intentionally-not-built-yet-phase-2--3-per-original-spec)
for exactly what's left and why.

### Frontend

```bash
cd apps/frontend
npm install
npm run dev   # http://localhost:3000, expects the API at NEXT_PUBLIC_API_URL (default localhost:8000)
```

Screens: Login/Register, Today (daily check-in), Timeline, Diff (+ Release
Notes and a downloadable share card), Profile (version generation, data
export/account deletion), Projects, Insights (interests/skills/skill graph/
behavior/anomalies/patterns), Ask Evolis. Auth token lives in
`localStorage`; no state library — plain `fetch` calls through
`apps/frontend/lib/api.ts`.

**Sign in with Google** is optional and off until you set it up: create an
OAuth 2.0 Client ID ("Web application") at
[console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials),
add your frontend origin (e.g. `http://localhost:3000`) under "Authorized
JavaScript origins", and set `GOOGLE_CLIENT_ID` in `.env`. The frontend
picks it up automatically from `GET /auth/google/config` — no separate
frontend env var needed. Leave it unset and the login page just shows
email/password, nothing broken.
