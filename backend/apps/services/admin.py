"""
Конфигурация административного интерфейса приложения услуг (services).
Регистрирует модели:
- ServiceCategory
- Service
Обеспечивает удобное управление каталогом услуг:
- фильтрация и поиск;
- inline-редактирование флагов и порядка;
- bulk-действия (actions);
- оптимизация запросов в админке.
"""

from django.contrib import admin

from .models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели ServiceCategory.
    Возможности:
        - inline-редактирование порядка (order) и активности (is_active);
        - фильтрация по активности;
        - поиск по названию и slug;
        - автогенерация slug из name.
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
    Админ-интерфейс для модели Service.

    Возможности:
        - быстрое включение/выключение услуги;
        - управление флагом отображения на главной странице (is_featured);
        - ручная сортировка featured-услуг;
        - оптимизация запросов через select_related(category);
        - массовые действия (bulk actions).
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
        Переопределяет queryset админки.
        Использует select_related("category") для уменьшения
        количества SQL-запросов при отображении списка услуг.
        """
        qs = super().get_queryset(request)
        return qs.select_related("category")

    @admin.action(description="Сделать активными")
    @admin.action(description="Сделать активными")
    def make_active(self, request, queryset):
        """
        Массовое действие.
        Устанавливает is_active=True для выбранных услуг.
        """
        queryset.update(is_active=True)

    @admin.action(description="Сделать неактивными")
    @admin.action(description="Сделать неактивными")
    def make_inactive(self, request, queryset):
        """
        Массовое действие.
        Устанавливает is_active=False для выбранных услуг.
        """
        queryset.update(is_active=False)

    @admin.action(description="Показывать на главной (featured = True)")
    @admin.action(description="Показывать на главной (featured = True)")
    def set_featured(self, request, queryset):
        """
        Массовое действие.
        Включает отображение выбранных услуг на главной странице.
        """
        queryset.update(is_featured=True)

    @admin.action(description="Убрать с главной (featured = False)")
    @admin.action(description="Убрать с главной (featured = False)")
    def unset_featured(self, request, queryset):
        """
        Массовое действие.
        Отключает отображение услуг на главной странице
        и сбрасывает порядок featured_order в 0.
        """
        queryset.update(is_featured=False, featured_order=0)
