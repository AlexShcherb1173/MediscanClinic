#!/usr/bin/env bash
set -euo pipefail

cd /app/backend

echo "==> wait for db"
python - <<'PY'
import os, time
import psycopg
host=os.getenv("DB_HOST","db")
port=int(os.getenv("DB_PORT","5432"))
name=os.getenv("DB_NAME","mediscan_db")
user=os.getenv("DB_USER","mediscan")
pwd=os.getenv("DB_PASSWORD","")
for i in range(60):
    try:
        psycopg.connect(host=host, port=port, dbname=name, user=user, password=pwd).close()
        print("DB OK")
        break
    except Exception as e:
        time.sleep(1)
else:
    raise SystemExit("DB not ready")
PY

echo "==> migrate"
python manage.py migrate --noinput

echo "==> collectstatic"
python manage.py collectstatic --noinput

echo "==> start: $*"
exec "$@"