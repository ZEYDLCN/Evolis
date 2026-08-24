#!/bin/sh
# Dev-only entrypoint. Detects GitHub Codespaces and points
# NEXT_PUBLIC_API_URL at the API's forwarded Codespaces URL instead of
# localhost:8000, since the browser is not on the same host as the
# container. Plain local Docker use (CODESPACE_NAME unset) just runs
# `npm run dev` with whatever NEXT_PUBLIC_API_URL is already set to.
set -e

if [ -n "$CODESPACE_NAME" ]; then
  export NEXT_PUBLIC_API_URL="https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
  echo "[entrypoint] GitHub Codespaces detected -> NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL"
  echo "NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL" > .env.local
fi

exec npm run dev
