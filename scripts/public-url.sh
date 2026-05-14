#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
URL=""
ATTEMPTS=0

echo "Waiting for tunnel URL..."
while [ -z "$URL" ] && [ "$ATTEMPTS" -lt 15 ]; do
    URL="$(docker compose -f "$REPO_DIR/docker-compose.yml" logs cloudflared 2>&1 \
        | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' \
        | tail -1)"
    ATTEMPTS=$((ATTEMPTS + 1))
    [ -z "$URL" ] && sleep 2
done

if [ -z "$URL" ]; then
    echo "ERROR: tunnel URL not found after ${ATTEMPTS} attempts." >&2
    echo "Run 'docker compose logs cloudflared' to debug." >&2
    exit 1
fi

echo "$URL"
