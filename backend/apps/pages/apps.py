"""
Конфигурация приложения страниц (pages).
Отвечает за регистрацию приложения в Django-проекте.
"""

from django.apps import AppConfig


class PagesConfig(AppConfig):
    """
    Конфигурация Django-приложения pages.
    Определяет:
        - default_auto_field — тип автоинкрементного первичного ключа по умолчанию;
        - name — Python-путь к приложению внутри проекта.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pages"
