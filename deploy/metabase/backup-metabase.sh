#!/bin/sh
# backup-metabase.sh — custom-format dump of the Metabase application DB.
# Run on the VPS host (needs the libpq client: pg_dump/pg_restore).
# Cron example (daily 03:20, keep 14 days):
#   20 3 * * * /srv/metabase/backup-metabase.sh >>/var/log/metabase-backup.log 2>&1
set -eu

: "${MB_DB_HOST:?set MB_DB_HOST (VPS PostgreSQL address)}"
MB_DB_PORT="${MB_DB_PORT:-5432}"
MB_DB_DBNAME="${MB_DB_DBNAME:-metabase}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/metabase}"
KEEP_DAYS="${KEEP_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
OUT="$BACKUP_DIR/metabase-appdb-$(date +%Y%m%d-%H%M%S).dump"

# Password via PGPASSWORD env (preferred) or ~/.pgpass, never on the command line.
pg_dump -h "$MB_DB_HOST" -p "$MB_DB_PORT" -U postgres -Fc \
  -f "$OUT" "$MB_DB_DBNAME"

find "$BACKUP_DIR" -name 'metabase-appdb-*.dump' -mtime +"$KEEP_DAYS" -delete
echo "wrote $OUT"

# Restore (stops Metabase first; key MB_ENCRYPTION_SECRET_KEY must match):
#   docker compose stop metabase
#   pg_restore -h "$MB_DB_HOST" -U postgres -c -d "$MB_DB_DBNAME" "$OUT"
#   docker compose start metabase
