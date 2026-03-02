"""
Конфигурация приложения пациентов (patients).
Отвечает за регистрацию приложения в Django-проекте.
"""

from django.apps import AppConfig


class PatientsConfig(AppConfig):
    """
    Конфигурация Django-приложения patients.
    Определяет:
        - default_auto_field — тип автоинкрементного первичного ключа по умолчанию;
        - name — Python-путь к приложению внутри проекта.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.patients"
