"""
Конфигурация приложения контактов (contacts).
Определяет параметры подключения приложения к Django-проекту.
"""

from django.apps import AppConfig


class ContactsConfig(AppConfig):
    """
    Конфигурация Django-приложения contacts.
    Задаёт:
        - default_auto_field — тип автоинкрементного первичного ключа по умолчанию;
        - name — Python-путь к приложению внутри проекта.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contacts"
