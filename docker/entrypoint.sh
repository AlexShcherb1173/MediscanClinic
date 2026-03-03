#!/usr/bin/env bash
set -euo pipefail

cd /app/backend

echo "==> migrate"
python manage.py migrate --noinput

echo "==> collectstatic"
python manage.py collectstatic --noinput

echo "==> start: $*"
exec "$@"