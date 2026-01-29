from django.contrib import admin
from .models import Promo


@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ("title", "badge", "is_active", "starts_at", "ends_at", "sort_order")
    list_filter = ("is_active", "badge")
    search_fields = ("title", "subtitle", "description", "badge", "slug")
    ordering = ("sort_order", "-created_at")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_active", "sort_order")