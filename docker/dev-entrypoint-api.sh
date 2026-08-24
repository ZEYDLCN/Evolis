#!/bin/sh
# Dev-only entrypoint (docker-compose.yml overrides the image's CMD with
# this): same migration step as the production CMD, plus --reload for
# live code editing. CORS is wide open here (see docker-compose.yml's
# CORS_ALLOWED_ORIGINS: "*") since this never runs in production —
# docker-compose.prod.yml uses the image's own CMD instead, unreloaded and
# without this override.
set -e

alembic upgrade head
exec uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
