"""
App configuration for services application.
"""

from django.apps import AppConfig


class ServicesConfig(AppConfig):
    """
    Django AppConfig for the services app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.services"
