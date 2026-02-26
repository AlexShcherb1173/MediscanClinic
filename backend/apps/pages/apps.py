"""
App configuration for pages application.

Responsible for registering the pages app
within the Django project.
"""

from django.apps import AppConfig


class PagesConfig(AppConfig):
    """
    Django AppConfig for the pages app.

    Defines:
    - default primary key field type
    - application dotted path
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pages"