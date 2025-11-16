#!/usr/bin/env bash
set -euo pipefail

echo "[backend] Waiting for Postgres at $DATABASE_URL..."
# Extract host and port for pg_isready using regex
DB_HOST=${DATABASE_URL##*@}
DB_HOST=${DB_HOST%%/*}
DB_HOST=${DB_HOST%%:*}
DB_PORT_TMP=${DATABASE_URL##*:}
DB_PORT=${DB_PORT_TMP%%/*}

# Fallbacks if parsing fails
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

for i in {1..60}; do
  if pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; then
    echo "[backend] Postgres is ready"
    break
  fi
  echo "[backend] Waiting for db ($i/60) ..."
  sleep 2
  if [ "$i" -eq 60 ]; then
    echo "[backend] ERROR: Database not ready in time" >&2
    exit 1
  fi
done

# Run migrations
if command -v alembic >/dev/null 2>&1; then
  echo "[backend] Running Alembic migrations..."
  alembic upgrade head || { echo "[backend] Alembic failed" >&2; exit 1; }
else
  echo "[backend] Alembic not found, skipping migrations"
fi

# Optional seed on first run
if [ "${AUTO_SEED:-false}" = "true" ]; then
  echo "[backend] Seeding database..."
  python scripts/seed_data.py || echo "[backend] Seeding failed (continuing)"
fi

# Start server
echo "[backend] Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 ${UVICORN_RELOAD:+--reload}
