"""
App configuration for promos application.
"""

from django.apps import AppConfig


class PromosConfig(AppConfig):
    """Django AppConfig for promos app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.promos"
