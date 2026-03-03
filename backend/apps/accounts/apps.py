"""
Конфигурация приложения accounts.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Класс конфигурации Django-приложения accounts.
    Определяет:
    - путь к приложению
    - человекочитаемое имя (label)
    - тип автоинкрементного поля по умолчанию
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
