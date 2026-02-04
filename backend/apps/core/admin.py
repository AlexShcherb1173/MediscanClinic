from django.contrib import admin
from .models import City, SiteSettings
from .models import License


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "phone")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "email", "telegram_bot_url")

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "sort_order", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title",)
    list_editable = ("is_active", "sort_order")