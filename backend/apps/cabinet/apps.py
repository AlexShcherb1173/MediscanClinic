"""
Конфигурация приложения личного кабинета (cabinet).
Определяет параметры подключения приложения к Django-проекту.
"""

from django.apps import AppConfig


class CabinetConfig(AppConfig):
    """
    Конфигурация Django-приложения cabinet.
    Задаёт:
        - default_auto_field — тип автоинкрементного первичного ключа по умолчанию;
        - name — Python-путь к приложению внутри проекта.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cabinet"
