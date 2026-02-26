"""
Admin configuration for patients application.
"""

from __future__ import annotations

from django.contrib import admin

from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "birth_date")
    search_fields = ("user__phone", "user__full_name", "user__email")
    list_select_related = ("user",)