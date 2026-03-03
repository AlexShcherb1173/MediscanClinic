"""
Конфигурация админ-интерфейса приложения результатов (results).
Настраивает отображение и поиск модели ResearchResult
в административной панели Django.
"""

from django.contrib import admin

from .models import ResearchResult


@admin.register(ResearchResult)
class ResearchResultAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели ResearchResult.
    Возможности:
        - отображение ключевых полей результата исследования;
        - фильтрация по дате результата и дате создания;
        - поиск по названию исследования и данным пациента;
        - оптимизация запросов через list_select_related.
    """

    list_display = ("id", "patient", "title", "result_date", "created_at")
    list_filter = ("result_date", "created_at")
    search_fields = ("title", "patient__phone", "patient__full_name", "patient__email")
    list_select_related = ("patient",)
