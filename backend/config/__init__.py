"""
Инициализация пакета проекта `config`.
Этот модуль экспортирует Celery-приложение как `celery_app`, чтобы Django и Celery
могли автоматически обнаруживать задачи (autodiscovery).
Важно:
    Импорт выполняется намеренно на уровне модуля. Даже если `celery_app` не
    используется напрямую в этом файле, он должен быть доступен снаружи пакета.
"""

from __future__ import annotations

from celery import Celery

celery_app: Celery | None

try:
    from .celery import app as _celery_app
except Exception:
    celery_app = None
else:
    celery_app = _celery_app

__all__ = ("celery_app",)
