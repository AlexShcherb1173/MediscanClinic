# ---------- base ----------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# ---------- lint ----------
FROM base AS lint

COPY backend/requirements-dev.txt /app/backend/requirements-dev.txt
RUN pip install --no-cache-dir -r /app/backend/requirements-dev.txt

COPY backend /app/backend
WORKDIR /app/backend

CMD ["bash", "-lc", "black apps config --check && isort apps config --check-only && flake8 apps config --config .flake8 && mypy apps config --config-file mypy.ini && pytest -q"]

# ---------- frontend (tailwind) ----------
FROM node:20-alpine AS frontend
WORKDIR /app/backend

COPY backend/package.json backend/package-lock.json backend/tailwind.config.js ./
COPY backend/static_src ./static_src

RUN npm ci
RUN npm run build:css

# ---------- runtime ----------
FROM base AS runtime

COPY backend /app/backend

# подменяем собранный css
COPY --from=frontend /app/backend/static/css/app.css /app/backend/static/css/app.css

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app/backend

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]