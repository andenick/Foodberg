#!/bin/bash
set -e

# Foodberg Docker Entrypoint
# Handles database restoration and Litestream replication

DB_PATH="/app/foodberg.db"

# If database doesn't exist, try to restore from Litestream replica
if [ ! -f "$DB_PATH" ]; then
    echo "Database not found, attempting restore from Litestream..."

    if [ -n "$LITESTREAM_BUCKET" ]; then
        litestream restore -if-replica-exists -config /etc/litestream.yml "$DB_PATH" || true
    fi

    if [ ! -f "$DB_PATH" ]; then
        echo "No backup found, starting with empty database"
        # The app will create the database on first run
    else
        echo "Database restored successfully"
    fi
fi

# Start Litestream replication in background, then start the app
if [ -n "$LITESTREAM_BUCKET" ]; then
    echo "Starting Litestream replication..."
    exec litestream replicate -config /etc/litestream.yml -exec "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
else
    echo "LITESTREAM_BUCKET not set, running without replication"
    exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
fi
