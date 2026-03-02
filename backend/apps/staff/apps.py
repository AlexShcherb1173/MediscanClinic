"""
Конфигурация приложения персонала (staff).
Отвечает за регистрацию приложения в Django-проекте.
"""

from django.apps import AppConfig


class StaffConfig(AppConfig):
    """
    Конфигурация Django-приложения staff.
    Определяет:
        - default_auto_field — тип автоинкрементного первичного ключа;
        - name — Python-путь к приложению внутри проекта.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.staff"
