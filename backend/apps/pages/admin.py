"""
Admin configuration for pages application.

Provides admin interface for managing CMS-like static pages,
including slug auto-generation and frontend preview link.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """
    Admin interface for Page model.

    Features:
    - Slug auto-population from title
    - Publish toggle
    - Content search
    - Preview link to frontend page
    """

    list_display = ("title", "slug", "is_published", "preview_link")
    list_filter = ("is_published",)
    search_fields = ("title", "slug", "content")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("slug",)

    fieldsets = (
        ("Основное", {"fields": ("title", "slug", "is_published")}),
        (
            "Контент (HTML / Tailwind)",
            {
                "fields": ("content",),
                "description": (
                    "Можно вставлять HTML. Рекомендуется оборачивать в "
                    "<code>&lt;div class='prose max-w-none'&gt;...&lt;/div&gt;</code> "
                    "и использовать <code>not-prose</code> для карточек/гридов."
                ),
            },
        ),
    )

    def preview_link(self, obj: Page):
        """
        Generate frontend preview link for the page.

        Uses slug-based routing: /page/<slug>/
        """
        if not obj.slug:
            return "-"

        return format_html(
            "<a href='/page/{}/' target='_blank'>Открыть</a>",
            obj.slug,
        )

    preview_link.short_description = "Превью"