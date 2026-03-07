# ---------- base ----------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
  && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements_.txt

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
# Tailwind content scanning — чтобы классы не вырезались, нужны шаблоны/аппы
COPY backend/templates ./templates
COPY backend/apps ./apps
COPY backend/static_src ./static_src
COPY backend/static ./static
RUN npm ci
RUN npm run build:css

# ---------- runtime ----------
# ---------- runtime ----------
FROM base AS runtime

# гарантируем ключевые файлы
COPY backend/manage.py /app/backend/manage.py
COPY backend/config /app/backend/config
COPY backend/apps /app/backend/apps
COPY backend/templates /app/backend/templates
COPY backend/static /app/backend/static
COPY backend/static_src /app/backend/static_src
COPY backend/__init__.py /app/backend/__init__.py

# (опционально) если есть другие корневые файлы в backend
COPY backend/mypy.ini /app/backend/mypy.ini
COPY backend/.flake8 /app/backend/.flake8
COPY backend/.coveragerc /app/backend/.coveragerc

# собранный css
COPY --from=frontend /app/backend/static/css/app.css /app/backend/static/css/app.css

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app/backend

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]
