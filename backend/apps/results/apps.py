"""
Конфигурация приложения результатов исследований (results).
Отвечает за:
- регистрацию приложения в Django;
- подключение сигналов при старте проекта.
"""

from django.apps import AppConfig


class ResultsConfig(AppConfig):
    """
    Конфигурация Django-приложения results.
    Определяет:
        - default_auto_field — тип автоинкрементного первичного ключа;
        - name — Python-путь к приложению;
        - verbose_name — человекочитаемое имя в админке;
        - ready() — подключение сигналов при инициализации приложения.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.results"
    verbose_name = "Результаты исследований"

    def ready(self):
        from . import signals  # noqa: F401
