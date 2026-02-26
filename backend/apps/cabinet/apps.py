"""
App configuration for cabinet application.
"""

from django.apps import AppConfig


class CabinetConfig(AppConfig):
    """Django AppConfig for cabinet app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cabinet"