"""
App configuration for appointments application.
"""

from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    """Django AppConfig for appointments app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.appointments"
