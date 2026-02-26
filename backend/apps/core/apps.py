"""
App configuration for core application.

Defines application metadata and default settings.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Django AppConfig for the core app.

    Responsible for:
    - Registering the application
    - Defining default primary key field type
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"