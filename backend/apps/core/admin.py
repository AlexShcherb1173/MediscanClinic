"""
Admin configuration for core application.

Registers:
- City
- SiteSettings
- License

Provides list display configuration,
filters and search capabilities
for convenient content management.
"""

from django.contrib import admin

from .models import City, SiteSettings, License


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """
    Admin interface for City model.

    Allows:
    - Viewing city name, phone and active status
    - Filtering by active flag
    - Searching by name and phone
    """

    list_display = ("name", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "phone")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for global SiteSettings.

    Intended to manage a single configuration object
    containing site-wide information.
    """

    list_display = ("site_name", "email", "telegram_bot_url")


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    """
    Admin interface for License model.

    Provides:
    - Quick visibility control
    - Inline editing of sort order and active flag
    - Filtering and search by title
    """

    list_display = ("title", "is_active", "sort_order", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title",)
    list_editable = ("is_active", "sort_order")