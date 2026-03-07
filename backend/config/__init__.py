"""
Инициализация пакета проекта `config`.
Этот модуль экспортирует Celery-приложение как `celery_app`, чтобы Django и Celery
могли автоматически обнаруживать задачи (autodiscovery).
Важно:
    Импорт выполняется намеренно на уровне модуля. Даже если `celery_app` не
    используется напрямую в этом файле, он должен быть доступен снаружи пакета.
"""

try:
    from .celery import app as celery_app  # noqa: F401
except Exception:
    # mypy/pre-commit env может быть без celery, и это ок
    celery_app = None

__all__ = ("celery_app",)
