"""
Конфигурация Django Admin для приложения личного кабинета (cabinet).
Содержит настройки отображения модели UserProfile в административной панели.
"""

from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели UserProfile.
    Настройки:
        - list_display: отображает ID профиля, связанного пользователя и Telegram chat_id.
        - search_fields: позволяет искать по телефону пользователя, ФИО и Telegram chat_id.
        - list_select_related: оптимизирует запросы к связанному объекту user.
    """

    list_display = ("id", "user", "telegram_chat_id")
    search_fields = ("user__phone", "user__full_name", "telegram_chat_id")
    list_select_related = ("user",)
