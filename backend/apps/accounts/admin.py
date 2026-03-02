"""
Административная конфигурация кастомной модели пользователя.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Настройка интерфейса Django Admin для модели User.
    Особенности:
    - Авторизация по номеру телефона
    - Отображение ФИО, телефона и email в списке
    - Управление правами доступа и статусом пользователя
    """

    ordering = ("id",)
    list_display = ("id", "full_name", "phone", "email", "is_staff", "is_active")
    search_fields = ("phone", "full_name", "email")

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Персональные данные", {"fields": ("full_name", "email")}),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "full_name",
                    "phone",
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")
