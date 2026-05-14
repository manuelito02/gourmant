#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="/mnt/d/work/gourmant-backups"
KEEP=7

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
DIR="$BACKUP_ROOT/$TIMESTAMP"

# Verify the db container is running before doing anything.
if ! docker compose -f "$REPO_DIR/docker-compose.yml" ps db | grep -q "Up"; then
    echo "ERROR: db container is not running. Start with 'docker compose up -d' first." >&2
    exit 1
fi

mkdir -p "$DIR"
echo "[backup] Writing to $DIR"

echo "[backup] Dumping database..."
docker compose -f "$REPO_DIR/docker-compose.yml" exec -T db \
    pg_dump -U gourmant -Fc gourmant > "$DIR/gourmant.dump"

echo "[backup] Archiving uploads..."
tar -czf "$DIR/uploads.tar.gz" -C "$REPO_DIR" uploads/

DUMP_SIZE="$(du -sh "$DIR/gourmant.dump" | cut -f1)"
UPL_SIZE="$(du -sh "$DIR/uploads.tar.gz" | cut -f1)"
RECIPE_COUNT="$(docker compose -f "$REPO_DIR/docker-compose.yml" exec -T db \
    psql -U gourmant -Atc "SELECT COUNT(*) FROM recipes;" gourmant)"
GIT_SHA="$(cd "$REPO_DIR" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")"

cat > "$DIR/manifest.txt" <<EOF
timestamp:    $TIMESTAMP
git_sha:      $GIT_SHA
recipe_count: $RECIPE_COUNT
dump_size:    $DUMP_SIZE
uploads_size: $UPL_SIZE
EOF

echo "[backup] Manifest:"
cat "$DIR/manifest.txt"

# Prune oldest bundles, keeping only the most recent $KEEP.
EXISTING="$(ls -1t "$BACKUP_ROOT" | tail -n +$((KEEP + 1)))"
if [ -n "$EXISTING" ]; then
    echo "[backup] Pruning old bundles..."
    echo "$EXISTING" | xargs -I{} rm -rf "$BACKUP_ROOT/{}"
fi

echo "[backup] Done. Bundle: $DIR"
