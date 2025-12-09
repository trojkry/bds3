#!/bin/bash

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="postgres"
DB_USER="postgres"
export PGPASSWORD="admin"

S3_BUCKET="s3://bds-backup-trojak"


echo "Načítání seznamu záloh z cloudu ($S3_BUCKET)..."

mapfile -t BACKUPS < <(aws s3 ls "$S3_BUCKET/" | grep -v "PRE" | awk '{print $4}' | sort -r)

if [ ${#BACKUPS[@]} -eq 0 ]; then
    echo "Chyba: V kýblu nejsou žádné zálohy."
    exit 1
fi

i=1
for backup in "${BACKUPS[@]}"; do
    echo "[$i] $backup"
    ((i++))
done

read -p "Zadejte ČÍSLO zálohy v kýblu, kterou chcete obnovit: " SELECTION

if ! [[ "$SELECTION" =~ ^[0-9]+$ ]] || [ "$SELECTION" -lt 1 ] || [ "$SELECTION" -gt "${#BACKUPS[@]}" ]; then
    echo "Chyba: Neplatná volba. Spusťte skript znovu."
    exit 1
fi

BACKUP_FILENAME="${BACKUPS[$((SELECTION-1))]}"
LOCAL_FILE="./$BACKUP_FILENAME"

echo "Vybráno: $BACKUP_FILENAME"
echo "Leju z kýblu"

aws s3 cp "$S3_BUCKET/$BACKUP_FILENAME" "$LOCAL_FILE"

if [ ! -f "$LOCAL_FILE" ]; then
    echo "[ERROR] Soubor se nepodařilo stáhnout."
    exit 1
fi

echo "Obnovuji databázi $DB_NAME..."
sleep 2

pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v --clean --if-exists "$LOCAL_FILE"
RESTORE_EXIT_CODE=$?

rm "$LOCAL_FILE"
echo "Uklizeno"


if [ $RESTORE_EXIT_CODE -eq 0 ]; then
    echo "[OK] Obnova proběhla úspěšně."
else
    echo "[INFO] Obnova dokončena (s chybou: $RESTORE_EXIT_CODE)."
fi