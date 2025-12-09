#!/bin/bash

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="postgres"
DB_USER="postgres"
export PGPASSWORD="admin"  

S3_BUCKET="s3://bds-backup-trojak"

BACKUP_DIR="$(dirname "$0")"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.dump"

echo "[$(date)] zaloha databaze $DB_NAME..."

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -F c -b -v -f "$BACKUP_FILE" "$DB_NAME"

if [ $? -eq 0 ]; then
  echo "[OK] Lokalni zaloha vytvorena: $BACKUP_FILE"
  
  echo "Odesilani na kýbl ($S3_BUCKET)..."
  aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/"
  
  if [ $? -eq 0 ]; then
      echo "[OK] Uspesne nahrano na S3 kýbl."
      
      rm "$BACKUP_FILE"
      echo "[INFO]S oubor smazan."
  else
      echo "[ERROR] Chyba pri nahravani na S3 kýbl"
      exit 1
  fi
  
else
  echo "[ERROR] Chyba pri lokalnim zalohovani (pg_dump) neposlalo se to na kýbl."
  exit 1
fi