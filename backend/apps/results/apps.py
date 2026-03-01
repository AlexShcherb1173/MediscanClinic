"""
App configuration for results application.

Imports signals in ready() to activate Telegram notifications.
"""

from django.apps import AppConfig


class ResultsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.results"
    verbose_name = "Результаты исследований"

    def ready(self):
        from . import signals  # noqa: F401
