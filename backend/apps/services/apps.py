"""
Конфигурация приложения услуг (services).
Отвечает за регистрацию приложения в Django-проекте.
"""

from django.apps import AppConfig


class ServicesConfig(AppConfig):
    """
    Конфигурация Django-приложения services.
    Определяет:
        - default_auto_field — тип автоинкрементного первичного ключа;
        - name — Python-путь к приложению внутри проекта.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.services"
