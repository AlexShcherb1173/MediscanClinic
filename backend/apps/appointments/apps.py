"""
Конфигурация приложения appointments.
"""

from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    """
    Класс конфигурации Django для приложения appointments.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.appointments"
