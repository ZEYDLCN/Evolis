# LifeDiff — Architecture & Product Notes

> **LifeDiff turns your daily activity into a version history of yourself.**

This document is the working reference for what's built and why. It's the
expanded, implementation-facing version of the original product spec.

## 1. Product in one loop

```
Daily natural-language entry
        -> LLM structured extraction   (topics, activities, blockers, status)
        -> Postgres                    (entries, topics, activities, projects)
        -> Embedding generation        (multilingual, entry-level)
        -> Topic/interest analysis     (deterministic scoring, section below)
        -> Temporal aggregation        (weekly/monthly rollups)
        -> Version snapshot            (a "YOU vX.Y")
        -> Diff engine                 (snapshot A vs snapshot B)
        -> Dashboard / Release Notes / Ask LifeDiff
```

## 2. The one rule everything else follows

```
LLM != Analytics Engine
```

The LLM is used **only** for: structured extraction from free text, naming
an already-discovered topic cluster, planning which analytics tool to call,
and phrasing a computed result as prose. Every number a user sees —
interest scores, skill scores, completion rate, deep work hours, context
switching, diffs — is computed by SQL/statistics/ML code that a test can
assert on deterministically. This is why `src/agents/verifier.py` exists: it
rejects any LLM-authored number that doesn't trace back to the analysis
payload it was given, falling back to a template-based (fully grounded)
answer instead.

This matters for the product, not just for engineering hygiene: a "your
focus time is up 34%" claim has to be *true*, or the whole diff-as-identity
concept collapses into astrology.

## 3. Repository layout

```
apps/
  api/            FastAPI app: routers, dependencies, config
  worker/         Celery app + background tasks
  frontend/       Next.js scaffold (Today/Timeline/Diff/Profile/Projects/Insights/Ask)
src/
  database/       SQLAlchemy models + session management
  extraction/     LLM (or heuristic fallback) structured extraction
  embeddings/     Multilingual embedding generation + cosine similarity
  ml/
    clustering/   HDBSCAN (primary) / K-Means (baseline) topic discovery
    anomaly/      Rolling z-score + Isolation Forest
    scoring/      Interest score + skill score formulas
  analytics/      interests / skills / productivity / temporal aggregation (SQL-backed)
  versions/       snapshot generation + diff engine
  rag/            hybrid (vector + keyword) retrieval over past entries
  agents/         Ask LifeDiff pipeline: classifier -> planner -> analyst -> verifier
  services/       auth, entry ingestion, project rollups
  monitoring/     metrics hooks (Prometheus-shaped, see section 8)
tests/
docs/
docker/
```

## 4. Data model

See `src/database/models.py`. Tables: `users`, `entries`, `entry_topics`,
`activities`, `projects`, `skills`, `goals`, `embeddings`, `clusters`,
`versions`, `version_metrics`, `insights`, `focus_sessions`, `tasks` —
matching the spec's section 30. `completion_rate`
(`src/analytics/productivity.py`) prefers `Task` rows for the requested
period and falls back to `Entry.completion_status` (done vs
partial/blocked/none) when a user hasn't created any tasks yet — see the
`source` field in `GET /analytics/behavior`.

Schema changes go through Alembic (`migrations/`), not
`Base.metadata.create_all` — `alembic upgrade head` against `DATABASE_URL`.
`init_db()` (still called on API startup) remains a convenience for local
dev/tests only.

Embeddings are stored as JSON float arrays by default (works on SQLite, zero
setup) and switch to a real pgvector `vector` column when
`EMBEDDING_BACKEND=pgvector` against a Postgres database — see
`src/database/models.py`. Similarity search (`src/rag/retriever.py`,
`src/embeddings/embedding_service.py::cosine_similarity`) works identically
either way from the caller's perspective; only the storage/query path
differs. Moving the JSON-backed cosine loop into a real pgvector `<->`
query once entry counts get large is a Phase 2 item.

## 5. Degradation strategy

Every AI/ML dependency is optional and has a deterministic fallback, so the
whole pipeline runs offline with `pip install -r requirements.txt` (no
Anthropic key, no sentence-transformers download, no HDBSCAN):

| Capability | Real backend | Fallback |
|---|---|---|
| Structured extraction | Claude API (`AnthropicExtractor`) | Regex/keyword heuristic (`HeuristicExtractor`) |
| Embeddings | multilingual-e5 via sentence-transformers | Deterministic hashing embedding |
| Clustering | HDBSCAN | K-Means, then no-op if scikit-learn is missing |
| Cluster naming | Claude API | Most frequent topic strings in the cluster (`" & "`-joined) |
| Anomaly detection | Isolation Forest | Rolling mean + z-score (always available) |
| Ask LifeDiff explanation | Claude API | Template built from the analysis payload |

This is a deliberate trade for an early-stage repo: correctness of the
*pipeline shape* now, swap in real models as they're wired up, without a
rewrite.

## 6. Ask LifeDiff pipeline

```
Question -> classify_query() -> build_plan() -> run_analysis()
         -> LLM explanation -> verify_grounded() -> Answer
```

Implemented as a plain function pipeline (`src/agents/orchestrator.py`)
rather than a LangGraph `StateGraph` for now — each stage already takes/
returns a plain dict, so wrapping it in LangGraph nodes later is mechanical.
Query classes: `interest_change`, `skill_progress`, `project_analysis`,
`behavior_pattern`, `timeline`, `comparison`, `search`.

## 7. API surface (current)

```
POST /auth/register, POST /auth/login
POST /entries, GET /entries
POST /projects, GET /projects, GET /projects/{id}/dashboard
POST /tasks, GET /tasks, POST /tasks/{id}/complete
GET  /timeline
GET  /analytics/interests, /analytics/skills, /analytics/behavior, /analytics/skill-graph
POST /clusters/rebuild, GET /clusters
POST /versions/generate, GET /versions
GET  /diff?base=<label>&target=<label>
POST /ask
```

All routes except `/auth/*` and `/health` require a bearer JWT and are
scoped to `request.user.id` — no cross-user reads are possible through the
service layer (see `src/services/*`, which always take `user_id`).

## 8. What's intentionally NOT built yet (Phase 2 / 3, per original spec)

Done since the initial MVP:
- ~~Alembic migrations~~ — `migrations/`, `alembic upgrade head`
- ~~Automatic cluster naming via LLM~~ — `src/ml/clustering/naming.py` +
  `src/services/cluster_service.py` persist `Cluster` rows and
  `EntryTopic.cluster_id`, exposed via `POST /clusters/rebuild`, `GET /clusters`
- ~~Real task-based completion tracking~~ — `Task` model + `/tasks`, feeding
  `completion_rate`
- ~~Skill Graph~~ — `src/analytics/skill_graph.py`: computed node metrics
  (unchanged from `skills.py`) plus a curated prerequisite edge list, filtered
  to skills the user actually has; `GET /analytics/skill-graph`

- ~~Frontend wired to the real API~~ — `apps/frontend`: login/register,
  Today (entry capture), Timeline, Diff, Profile (version generation),
  Projects, Insights (interests/skills/skill-graph/behavior), Ask LifeDiff.
  Plain `fetch` + `localStorage` JWT, no state library — small enough not to
  need one yet.

Still open, roughly in the order it's worth picking them up:
- Full LangGraph agent orchestration (current orchestrator is a plain
  function pipeline with the same stage boundaries — see § 6)
- Prometheus/Grafana/LangSmith wiring (`src/monitoring/` has the seam but is
  currently empty)
- Knowledge Graph (Neo4j)
- Mobile app, calendar import, git integration, social share cards

## 9. Running it

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

Or the full stack (Postgres + pgvector, Redis, worker, frontend):

```bash
docker compose up --build
```
