#!/usr/bin/env bash
# Runs on the Codespace/host machine *before* any container is built or
# started (VS Code's "initializeCommand" hook) — this is the only hook that
# fires early enough to guarantee .env exists before `docker compose up`
# tries to read it via env_file.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  # A random per-codespace secret beats the checked-in placeholder, even
  # though this is throwaway dev data — costs nothing to do properly.
  if command -v python3 >/dev/null 2>&1; then
    secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    # Portable in-place sed edit (works on both GNU and BSD sed).
    sed -i.bak "s#^SECRET_KEY=.*#SECRET_KEY=${secret}#" .env && rm -f .env.bak
  fi
  echo "[devcontainer] Created .env from .env.example"
fi
