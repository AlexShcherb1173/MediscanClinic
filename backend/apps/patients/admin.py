"""
Конфигурация Django Admin для приложения пациентов (patients).
Определяет отображение и поиск по профилям пациентов
в административной панели.
"""

from __future__ import annotations

from django.contrib import admin

from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели PatientProfile.
    Настройки:
        - list_display: отображение ID, связанного пользователя и даты рождения;
        - search_fields: поиск по телефону, ФИО и email пользователя;
        - list_select_related: оптимизация запроса к связанному объекту user.
    """
    list_display = ("id", "user", "birth_date")
    search_fields = ("user__phone", "user__full_name", "user__email")
    list_select_related = ("user",)
