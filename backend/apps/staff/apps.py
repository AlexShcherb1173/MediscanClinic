"""
App configuration for staff application.
"""

from django.apps import AppConfig


class StaffConfig(AppConfig):
    """Django AppConfig for staff app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.staff"