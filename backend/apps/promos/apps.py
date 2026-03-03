"""
Конфигурация приложения акций (promos).
Отвечает за регистрацию приложения в Django-проекте.
"""

from django.apps import AppConfig


class PromosConfig(AppConfig):
    """
    Конфигурация Django-приложения promos.
    Определяет:
        - default_auto_field — тип автоинкрементного первичного ключа по умолчанию;
        - name — Python-путь к приложению внутри проекта.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.promos"
