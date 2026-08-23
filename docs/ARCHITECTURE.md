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
GET  /analytics/interests, /analytics/skills, /analytics/behavior,
     /analytics/skill-graph, /analytics/anomalies, /analytics/patterns
POST /clusters/rebuild, GET /clusters
POST /versions/generate, GET /versions
GET  /diff?base=<label>&target=<label>
GET  /release-notes?base=<label>&target=<label>
GET  /release-notes/card?base=<label>&target=<label>   (image/svg+xml)
POST /ask
GET  /me/export, DELETE /me
GET  /graph/export, POST /graph/sync
GET  /metrics                                          (Prometheus, unauthenticated)
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
  Projects, Insights (interests/skills/skill-graph/behavior/anomalies/
  patterns), Ask LifeDiff. Plain `fetch` + `localStorage` JWT, no state
  library — small enough not to need one yet.
- ~~Anomaly Detection~~ (§17) — `src/analytics/anomalies.py`: rolling
  8-week mean + z-score on weekly learning minutes (overall and per-topic);
  `GET /analytics/anomalies`
- ~~Pattern Detection~~ (§16) — `src/analytics/patterns.py`: Pearson
  correlation between weekly active-project-count and completion rate,
  reported strictly as association, never causation;
  `GET /analytics/patterns`
- ~~Release Notes For You~~ (§28) — `src/versions/release_notes.py` formats
  an existing `VersionDiff` into the spec's changelog shape (no new numbers,
  no LLM); `GET /release-notes?base=&target=`, rendered on the frontend's
  Diff page
- ~~Privacy: data export + account deletion~~ (§32) —
  `src/services/account_service.py`; `GET /me/export`, `DELETE /me`
  (explicit multi-table deletion, not an ORM cascade), wired into the
  frontend Profile page
- ~~Golden dataset + AI evaluation~~ (§37-38) —
  `tests/evaluation/golden_dataset.json` + `src/evaluation/extraction_eval.py`
  (topic P/R/F1, duration/activity/completion accuracy against any
  `Extractor`) and `src/evaluation/retrieval_eval.py` (Precision@K, Recall@K,
  MRR, generic over ranked id lists). Regression-guarded by
  `tests/evaluation/test_golden_dataset.py` on every test run. Building this
  harness caught and fixed a real bug: `HeuristicExtractor` was discarding
  a detected duration whenever no topic was found in the same sentence.
- ~~CI/CD~~ — `.github/workflows/ci.yml`: backend job runs
  `alembic upgrade head` + `alembic check` (fails if models drift from the
  latest migration) then the full pytest suite; frontend job runs
  `next build` (typecheck + static generation) on every push/PR to `main`
- ~~Full LangGraph agent orchestration~~ — `src/agents/graph.py`: Ask
  LifeDiff runs as a real `StateGraph` (classify → plan → analyze → explain
  → verify → END), compiled once and cached. `orchestrator.ask()` is still
  the stable entry point the API calls. Fixing the graph's own tests
  surfaced and fixed a real classifier bug: `\b...\b` word-boundary regexes
  silently rejected every inflected Turkish form of a stem (ilgi → ilgim,
  değiş → değiştim), permanently misrouting those questions to the
  `search` fallback.
- ~~Prometheus monitoring~~ (§36) — `src/monitoring/metrics.py`: HTTP
  request count/latency (FastAPI middleware), LLM calls by purpose/outcome,
  embedding generation time, background job time/errors. `GET /metrics`.
  LangSmith/Grafana wiring is a deployment-time addition on top of this,
  not more application code.
- ~~Clustering quality metrics~~ (§37) — `src/ml/clustering/quality.py`:
  silhouette score and rebuild-to-rebuild stability (Adjusted Rand Index),
  both optional (`None` without scikit-learn or with too few clusters).
  Returned from `POST /clusters/rebuild`.
- ~~Encryption at rest~~ (§32) — `src/database/encryption.py`: an opt-in
  (`ENCRYPTION_KEY`) SQLAlchemy `TypeDecorator` that transparently
  encrypts/decrypts `Entry.raw_text` (AES via `cryptography.fernet`) at the
  ORM boundary. Off by default so every existing test and deployment is
  unaffected. Trade-off made explicit in the module docstring: an encrypted
  column can't be searched with SQL `LIKE`, so
  `src/rag/retriever.py::keyword_search` branches to decrypt-then-filter in
  Python when encryption is on — fine at personal-analytics scale, not
  forever.
- ~~Social Share Cards~~ (§28, §41) — `src/versions/share_card.py` renders
  the existing `VersionDiff`/release-notes data as a self-contained SVG
  card (no image library, no server-side font rendering to get right).
  `GET /release-notes/card`, rendered + downloadable on the frontend's Diff
  page.
- ~~Knowledge Graph~~ (§25, explicitly optional per spec) —
  `src/graph/knowledge_graph.py` builds the USER→LEARNS→SKILL,
  USER→BUILDS→PROJECT, PROJECT→USES→SKILL, ENTRY→MENTIONS→TOPIC graph as
  plain JSON from already-computed data (no new source of truth);
  `GET /graph/export` always works. `src/graph/neo4j_sync.py` optionally
  pushes it into a real Neo4j instance when `NEO4J_URI` is set and the
  `neo4j` driver is installed — `POST /graph/sync` reports honestly when it
  skipped rather than pretending to have synced.

Still open:
- Mobile app, calendar import, git integration — each needs a real
  external account/OAuth app registration (App Store presence, a Google/
  Microsoft Calendar OAuth client, a GitHub OAuth app) that only the
  product's actual owner can set up; not something to fake credentials for
  in this environment. The architecture doesn't block them: calendar/git
  import would land as new `src/ingestion/` sources feeding the same
  `create_entry`/`Activity` pipeline everything else already goes through.
- Production deployment (a real target environment — cloud provider,
  domain, TLS — is a decision for whoever owns hosting, not something to
  invent here)
- LangSmith tracing wired to real LLM calls (needs a LangSmith account/key;
  the call sites are already instrumented for metrics in `src/monitoring/`,
  adding tracing there is small once there's somewhere to send it)

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
