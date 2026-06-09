#!/usr/bin/env bash
#
# restore_db.sh — Database restore for EYTGaming
#
# Usage:
#   ./scripts/restore_db.sh backups/eytgaming_db_20260601_120000.sql.gz
#   ./scripts/restore_db.sh --latest            # restore most recent backup
#   ./scripts/restore_db.sh --s3 <key>           # restore from S3
#
# Requirements: pg_restore (PostgreSQL client), gzip, optional: awscli
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

# Database config
DB_NAME="${DB_NAME:-eytgaming_db}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"

export PGPASSWORD="$DB_PASSWORD"

RESTORE_FILE=""

# Parse arguments
case "${1:-}" in
    --latest)
        RESTORE_FILE=$(ls -1t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head -1)
        if [ -z "$RESTORE_FILE" ]; then
            echo "[restore] ERROR: No backups found in $BACKUP_DIR" >&2
            exit 1
        fi
        echo "[restore] Using latest backup: $RESTORE_FILE"
        ;;
    --s3)
        S3_BUCKET="${S3_BUCKET:-s3://eytgaming-backups/db/}"
        S3_KEY="${2:-}"
        if [ -z "$S3_KEY" ]; then
            echo "[restore] ERROR: Specify S3 key as second argument" >&2
            exit 1
        fi
        RESTORE_FILE="$BACKUP_DIR/$(basename "$S3_KEY")"
        echo "[restore] Downloading from $S3_BUCKET$S3_KEY"
        aws s3 cp "$S3_BUCKET$S3_KEY" "$RESTORE_FILE"
        ;;
    *)
        RESTORE_FILE="${1:-}"
        if [ -z "$RESTORE_FILE" ] || [ ! -f "$RESTORE_FILE" ]; then
            echo "[restore] ERROR: Backup file not found: $RESTORE_FILE" >&2
            echo "Usage: $0 [--latest | --s3 <key> | <file>]" >&2
            exit 1
        fi
        ;;
esac

echo "[restore] WARNING: This will DESTROY the current '$DB_NAME' database"
echo "[restore] Press Ctrl+C to cancel or Enter to continue..."
read -r

echo "[restore] Terminating connections to $DB_NAME..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = '$DB_NAME'
      AND pid <> pg_backend_pid();
" 2>/dev/null || true

echo "[restore] Dropping and recreating $DB_NAME..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"

echo "[restore] Restoring from $RESTORE_FILE..."
pg_restore \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    --verbose \
    "$RESTORE_FILE"

echo "[restore] Restore complete"
echo "[restore] Run: python manage.py migrate  (if needed)"
echo "[restore] Run: python manage.py createsuperuser  (if admin user was lost)"
