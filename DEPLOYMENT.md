# Deploying Evolis

This covers taking Evolis from local dev (`docker-compose.yml`, SQLite,
`ENVIRONMENT=development`) to a real deployment: Postgres + pgvector, Redis,
the FastAPI backend, the Celery worker, and the Next.js frontend, all behind
a reverse proxy with TLS.

Evolis is deliberately self-hostable and platform-agnostic — the steps below
work on a single VM (a $5-20/mo box is plenty to start), and the same images
work unmodified on any container platform (ECS, Cloud Run, Fly.io, Railway,
a Kubernetes cluster) if you'd rather not run `docker compose` directly on a
host.

## 1. What you're deploying

| Service | Image | Notes |
|---|---|---|
| `evolis-api` | `docker/Dockerfile.api` | FastAPI, runs `alembic upgrade head` on every boot |
| `evolis-worker` | `docker/Dockerfile.worker` | Celery worker (async clustering, notifications) |
| `evolis-frontend` | `apps/frontend/Dockerfile` | Next.js, standalone production build |
| `postgres` | `pgvector/pgvector:pg16` | Postgres with the `pgvector` extension |
| `redis` | `redis:7-alpine` | Celery broker/result backend |

`docker-compose.prod.yml` wires all five together with production defaults
(no host-exposed DB/Redis ports, `restart: unless-stopped`, health checks).

## 2. Prerequisites

- A host (or platform) that can run Docker and docker-compose-v2.
- A domain (or two: e.g. `app.example.com` for the frontend,
  `api.example.com` for the backend) with DNS pointed at the host.
- A reverse proxy that terminates TLS — Caddy is the least ceremony
  (automatic Let's Encrypt certs from a two-line Caddyfile); nginx +
  certbot or Traefik work equally well. This repo doesn't ship one, since
  the right choice depends on what else runs on the host.

## 3. Configure

```bash
cp .env.production.example .env.production
```

Fill in every value marked `REPLACE_ME`. Required, or the API refuses to
boot (see `apps/api/main.py::_check_production_config`):

- `SECRET_KEY` — `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `POSTGRES_PASSWORD` — a long random password
- `CORS_ALLOWED_ORIGINS` — your real frontend origin(s), comma-separated,
  no wildcard
- `PUBLIC_API_URL` — your real backend origin; this gets baked into the
  frontend's client-side JS bundle at build time, so changing it later
  means rebuilding the frontend image, not just restarting a container

Recommended:

- `ENCRYPTION_KEY` — encrypts entry text at rest
  (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- `ANTHROPIC_API_KEY` — without it, extraction and Ask Evolis fall back to
  deterministic heuristics instead of real LLM calls (still fully
  functional, just less nuanced prose)
- `EMBEDDING_BACKEND=pgvector` — uses the Postgres pgvector extension
  instead of the JSON fallback, once you're on real Postgres anyway

## 4. Build and start

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

This builds all three application images, starts Postgres and Redis first
(with a healthcheck gate so the API doesn't race a not-yet-ready database),
then the API, worker, and frontend. The API container runs
`alembic upgrade head` on every start — safe to run repeatedly, a no-op once
the schema is current.

Check it's healthy:

```bash
docker compose -f docker-compose.prod.yml ps
curl http://127.0.0.1:8000/health   # {"status": "ok"}
curl http://127.0.0.1:3000          # 200
```

## 5. Put a reverse proxy in front

Both `evolis-api` and `evolis-frontend` publish only to `127.0.0.1` in
`docker-compose.prod.yml` — they are not reachable from the internet until
something proxies to them. A minimal Caddyfile:

```
app.your-domain.example {
    reverse_proxy 127.0.0.1:3000
}

api.your-domain.example {
    reverse_proxy 127.0.0.1:8000
}
```

Caddy issues and renews TLS certificates automatically. Restart Caddy after
DNS for both hosts resolves.

## 6. Migrations for future deploys

New Evolis releases may add Alembic migrations. Since the API container
already runs `alembic upgrade head` on boot, a normal redeploy handles this
automatically:

```bash
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

To run a migration manually (e.g. to inspect it before a deploy):

```bash
docker compose -f docker-compose.prod.yml run --rm evolis-api alembic upgrade head
```

## 7. Backups

Postgres data lives in the `evolis_pgdata` named volume. At minimum, take a
daily logical dump:

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U evolis evolis | gzip > "evolis-$(date +%F).sql.gz"
```

Store it off-host (S3, Backblaze, etc.) — a volume backup on the same disk
as the database doesn't protect against disk failure.

## 8. Monitoring

`GET /metrics` on the API exposes Prometheus-format metrics
(`http_requests_total`, `http_request_duration_seconds`, LLM call counts —
see `src/monitoring/metrics.py`). Point a Prometheus instance at it, or
scrape it manually to sanity-check request volume and error rates after a
deploy.

## 9. Scaling notes

The defaults here are sized for a single small VM. Before running more than
one API replica behind a load balancer, note two process-local pieces of
state that would need to move to Redis first:

- **Auth rate limiting** (`apps/api/rate_limit.py`) — currently an
  in-memory sliding window per process. Fine for one replica; a second
  replica just means the effective limit doubles, which isn't dangerous,
  just imprecise. Swap for a Redis-backed limiter if that matters to you.
- **JWT sessions** are stateless (HS256, no server-side session store), so
  those already scale horizontally with zero changes.

Postgres and Redis can each move to a managed service (RDS, Upstash, etc.)
by pointing `DATABASE_URL` / `REDIS_URL` at them — nothing in the app
assumes they're co-located containers.

## 10. Known gaps to be aware of

- No automated pagination on some list endpoints yet — fine at personal-use
  data volumes, worth revisiting before treating this as a multi-tenant
  SaaS product.
- JWT is a small hand-rolled HS256 implementation
  (`src/services/auth_service.py`) rather than a battle-tested library —
  deliberately minimal (see that file's docstring), but worth a proper
  security review before handling data you don't control yourself.
- No refresh-token flow: sessions simply expire after
  `ACCESS_TOKEN_EXPIRE_MINUTES` and the user logs in again.
