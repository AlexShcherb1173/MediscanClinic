from django.contrib import admin

from .models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active", "slug")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("order", "name")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 50


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    # Листинг
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

    # Быстрое редактирование прямо в списке
    list_editable = ("is_active", "is_featured", "featured_order")

    # Фильтры справа
    list_filter = ("is_active", "is_featured", "category")

    # Поиск
    search_fields = ("name", "slug", "description", "category__name")

    # Автослаг
    prepopulated_fields = {"slug": ("name",)}

    # Сортировка списка (featured сначала)
    ordering = ("-is_featured", "featured_order", "name")

    # Пагинация
    list_per_page = 50

    # Поля на форме (аккуратно сгруппировано)
    fieldsets = (
        ("Основное", {"fields": ("category", "name", "slug", "description")}),
        ("Цена", {"fields": ("price_from", "price_to")}),
        ("Статус", {"fields": ("is_active",)}),
        ("Главная страница", {"fields": ("is_featured", "featured_order")}),
    )

    # Удобство: действия
    actions = (
        "make_active",
        "make_inactive",
        "set_featured",
        "unset_featured",
    )

    def get_queryset(self, request):
        """
        Чуть оптимизируем админку: category уже select_related через list_select_related,
        но если где-то будет еще использование — держим единый get_queryset.
        """
        qs = super().get_queryset(request)
        return qs.select_related("category")

    @admin.action(description="Сделать активными")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Сделать неактивными")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Показывать на главной (featured = True)")
    def set_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="Убрать с главной (featured = False)")
    def unset_featured(self, request, queryset):
        queryset.update(is_featured=False, featured_order=0)