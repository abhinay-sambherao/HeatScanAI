#!/bin/bash
# Daily PostgreSQL backup script
# Usage: ./backup_db.sh
# Cron: 0 2 * * * /path/to/backup_db.sh

BACKUP_DIR="/var/backups/evh-heatscan"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="evh_heatscan_${TIMESTAMP}.sql.gz"
DAYS_TO_KEEP=30

mkdir -p "$BACKUP_DIR"

PGPASSWORD=evh_secret pg_dump -h localhost -U evh evh_heatscan | gzip > "$BACKUP_DIR/$FILENAME"

if [ $? -eq 0 ]; then
    echo "Backup successful: $FILENAME"
else
    echo "Backup FAILED" >&2
    exit 1
fi

find "$BACKUP_DIR" -name "evh_heatscan_*.sql.gz" -mtime +$DAYS_TO_KEEP -delete

echo "Old backups cleaned (kept $DAYS_TO_KEEP days)"
