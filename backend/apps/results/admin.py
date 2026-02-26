"""
Admin configuration for results application.
"""

from django.contrib import admin

from .models import ResearchResult


@admin.register(ResearchResult)
class ResearchResultAdmin(admin.ModelAdmin):
    """Admin UI for ResearchResult."""
    list_display = ("id", "patient", "title", "result_date", "created_at")
    list_filter = ("result_date", "created_at")
    search_fields = ("title", "patient__phone", "patient__full_name", "patient__email")
    list_select_related = ("patient",)