"""
Конфигурация Django Admin для приложения акций (promos).
Определяет отображение и управление объектами Promo
в административной панели.
"""

from django.contrib import admin

from .models import Promo


@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Promo.
    Возможности:
        - отображение основных полей (заголовок, бейдж, статус, даты, порядок сортировки);
        - фильтрация по активности и бейджу;
        - поиск по текстовым полям и slug;
        - автогенерация slug из title;
        - редактирование полей is_active и sort_order прямо в списке;
        - удобное управление связью с услугами (filter_horizontal).
    """

    list_display = ("title", "badge", "is_active", "starts_at", "ends_at", "sort_order")
    list_filter = ("is_active", "badge")
    search_fields = ("title", "subtitle", "description", "badge", "slug")
    ordering = ("sort_order", "-created_at")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_active", "sort_order")
    filter_horizontal = ("services",)
