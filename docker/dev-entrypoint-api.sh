#!/bin/sh
# Dev-only entrypoint (docker-compose.yml overrides the image's CMD with
# this). Detects GitHub Codespaces and, if the operator hasn't set
# CORS_ALLOWED_ORIGINS explicitly, points it at the frontend's forwarded
# Codespaces URL so the browser-origin check in apps/api/main.py doesn't
# reject the frontend's requests. Plain local Docker use (CODESPACE_NAME
# unset) is unaffected — CORS_ALLOWED_ORIGINS falls back to its normal
# localhost default.
set -e

if [ -n "$CODESPACE_NAME" ] && [ -z "$CORS_ALLOWED_ORIGINS" ]; then
  export CORS_ALLOWED_ORIGINS="https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
  echo "[entrypoint] GitHub Codespaces detected -> CORS_ALLOWED_ORIGINS=$CORS_ALLOWED_ORIGINS"
fi

alembic upgrade head
exec uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
