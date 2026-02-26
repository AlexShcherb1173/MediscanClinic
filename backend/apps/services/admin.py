"""
Admin configuration for services application.

Registers:
- ServiceCategory
- Service

Provides удобный интерфейс управления каталогом услуг:
фильтры, поиск, inline-редактирование и действия (actions).
"""

from django.contrib import admin

from .models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for ServiceCategory.

    Supports:
    - inline editing of order and active flag
    - filtering by is_active
    - searching by name/slug
    """

    list_display = ("name", "order", "is_active", "slug")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("order", "name")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 50


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Admin interface for Service.

    Features:
    - fast toggles for is_active/is_featured/featured_order
    - optimized queryset with select_related(category)
    - bulk actions for status and featured flag
    """

    list_display = (
        "name",
        "category",
        "price_from",
        "price_to",
        "is_active",
        "is_featured",
        "featured_order",
        "slug",
    )
    list_select_related = ("category",)
    list_editable = ("is_active", "is_featured", "featured_order")
    list_filter = ("is_active", "is_featured", "category")
    search_fields = ("name", "slug", "description", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-is_featured", "featured_order", "name")
    list_per_page = 50

    fieldsets = (
        ("Основное", {"fields": ("category", "name", "slug", "description")}),
        ("Цена", {"fields": ("price_from", "price_to")}),
        ("Статус", {"fields": ("is_active",)}),
        ("Главная страница", {"fields": ("is_featured", "featured_order")}),
    )

    actions = (
        "make_active",
        "make_inactive",
        "set_featured",
        "unset_featured",
    )

    def get_queryset(self, request):
        """
        Optimize admin queryset by selecting related category.
        """
        qs = super().get_queryset(request)
        return qs.select_related("category")

    @admin.action(description="Сделать активными")
    def make_active(self, request, queryset):
        """Bulk action: set is_active=True for selected services."""
        queryset.update(is_active=True)

    @admin.action(description="Сделать неактивными")
    def make_inactive(self, request, queryset):
        """Bulk action: set is_active=False for selected services."""
        queryset.update(is_active=False)

    @admin.action(description="Показывать на главной (featured = True)")
    def set_featured(self, request, queryset):
        """Bulk action: set is_featured=True for selected services."""
        queryset.update(is_featured=True)

    @admin.action(description="Убрать с главной (featured = False)")
    def unset_featured(self, request, queryset):
        """Bulk action: set is_featured=False and reset featured_order."""
        queryset.update(is_featured=False, featured_order=0)