#!/usr/bin/env bash
#
# backup_db.sh — Database backup for EYTGaming
#
# Usage:
#   ./scripts/backup_db.sh                    # backup with .env config
#   ./scripts/backup_db.sh --s3               # backup and upload to S3
#   ./scripts/backup_db.sh --local-only       # backup to local file only
#
# Requirements: pg_dump (PostgreSQL client), gzip, optional: awscli
# Source .env or set DB_* vars before running.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Database config (fall back to defaults)
DB_NAME="${DB_NAME:-eytgaming_db}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Backup destination
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"
S3_BUCKET="${S3_BUCKET:-s3://eytgaming-backups/db/}"

mkdir -p "$BACKUP_DIR"

export PGPASSWORD="$DB_PASSWORD"

echo "[backup] Starting backup of $DB_NAME@$DB_HOST:$DB_PORT"
echo "[backup] Output: $BACKUP_FILE"

pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_FILE"

if [ $? -eq 0 ]; then
    FILE_SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null || echo "unknown")
    echo "[backup] Backup complete: $BACKUP_FILE ($FILE_SIZE bytes)"
else
    echo "[backup] ERROR: Backup failed" >&2
    exit 1
fi

# Upload to S3 if requested
if [ "${1:-}" = "--s3" ] || [ "${1:-}" = "--s3-only" ]; then
    if command -v aws &>/dev/null; then
        echo "[backup] Uploading to $S3_BUCKET"
        aws s3 cp "$BACKUP_FILE" "$S3_BUCKET" --storage-class STANDARD_IA
        echo "[backup] Upload complete"
    else
        echo "[backup] WARNING: awscli not found, skipping S3 upload" >&2
    fi
fi

# Clean up old backups (keep last 30 days)
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +30 -delete
echo "[backup] Cleaned up backups older than 30 days"

# Keep only the latest 10 local backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/"${DB_NAME}"_*.sql.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 10 ]; then
    ls -1t "$BACKUP_DIR"/"${DB_NAME}"_*.sql.gz | tail -n +11 | xargs rm -f
    echo "[backup] Pruned to last 10 backups"
fi

echo "[backup] Done"
