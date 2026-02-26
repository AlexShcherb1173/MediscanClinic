"""
Admin configuration for cabinet application.
"""

from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin UI for UserProfile."""
    list_display = ("id", "user", "telegram_chat_id")
    search_fields = ("user__phone", "user__full_name", "telegram_chat_id")
    list_select_related = ("user",)