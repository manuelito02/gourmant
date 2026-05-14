#!/usr/bin/env bash
set -euo pipefail

BUNDLE="${1:-}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "$BUNDLE" ]; then
    echo "Usage: $0 <bundle-path>" >&2
    echo "  e.g. $0 /mnt/d/work/gourmant-backups/2026-05-14_143022" >&2
    exit 1
fi

if [ ! -d "$BUNDLE" ]; then
    echo "ERROR: bundle directory not found: $BUNDLE" >&2
    exit 1
fi
if [ ! -f "$BUNDLE/gourmant.dump" ]; then
    echo "ERROR: gourmant.dump not found in $BUNDLE" >&2
    exit 1
fi
if [ ! -f "$BUNDLE/uploads.tar.gz" ]; then
    echo "ERROR: uploads.tar.gz not found in $BUNDLE" >&2
    exit 1
fi

echo "Restoring from: $BUNDLE"
if [ -f "$BUNDLE/manifest.txt" ]; then
    echo "--- manifest ---"
    cat "$BUNDLE/manifest.txt"
    echo "----------------"
fi

echo ""
echo "WARNING: This will DESTROY all current data (DB + uploads) and replace it"
echo "with the contents of the bundle above."
echo ""
read -rp "Type 'yes' to continue: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "[restore] Stopping app container..."
docker compose -f "$REPO_DIR/docker-compose.yml" stop app

echo "[restore] Dropping and recreating database..."
docker compose -f "$REPO_DIR/docker-compose.yml" exec -T db \
    psql -U gourmant -c "DROP DATABASE IF EXISTS gourmant;" postgres
docker compose -f "$REPO_DIR/docker-compose.yml" exec -T db \
    psql -U gourmant -c "CREATE DATABASE gourmant OWNER gourmant;" postgres

echo "[restore] Restoring database dump..."
docker compose -f "$REPO_DIR/docker-compose.yml" exec -T db \
    pg_restore -U gourmant -d gourmant < "$BUNDLE/gourmant.dump"

echo "[restore] Restoring uploads..."
# Run inside a container so we have the same root permissions that wrote the files.
BUNDLE_ABS="$(realpath "$BUNDLE")"
docker run --rm \
    -v "$REPO_DIR/uploads:/uploads" \
    -v "$BUNDLE_ABS:/backup:ro" \
    alpine sh -c "rm -rf /uploads/* /uploads/.* 2>/dev/null; tar -xzf /backup/uploads.tar.gz --strip-components=1 -C /uploads"

echo "[restore] Starting app container..."
docker compose -f "$REPO_DIR/docker-compose.yml" start app

echo "[restore] Done. Restored from $BUNDLE"
