"""
App configuration for accounts application.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Django AppConfig for accounts app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
