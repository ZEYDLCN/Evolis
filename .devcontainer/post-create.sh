#!/usr/bin/env bash
# Runs once, inside the evolis-api container, after all compose services
# have been created for the first time.
set -euo pipefail
cd /app

echo "[devcontainer] Waiting for Postgres..."
for i in $(seq 1 30); do
  if python3 -c "
import sys, os
import psycopg
try:
    psycopg.connect(os.environ['DATABASE_URL'].replace('+psycopg', ''), connect_timeout=2).close()
except Exception:
    sys.exit(1)
" 2>/dev/null; then
    break
  fi
  sleep 1
done

echo "[devcontainer] Running migrations..."
alembic upgrade head

echo "[devcontainer] Ready. The API auto-reloads on save (see docker-compose.yml);"
echo "[devcontainer] the frontend container runs its own 'npm run dev' the same way."
echo "[devcontainer] Ports: 8000 = API, 3000 = frontend (see the Ports tab)."
