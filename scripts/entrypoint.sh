#!/bin/sh
set -eu
cd /app
if [ "${STORE_BACKEND:-memory}" = "postgres" ]; then
  python -m alembic upgrade head
fi
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
