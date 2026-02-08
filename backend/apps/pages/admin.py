from django.contrib import admin
from django.utils.html import format_html

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
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
        if not obj.slug:
            return "-"
        # у тебя URL: page/<slug:slug>/
        return format_html("<a href='/page/{}/' target='_blank'>Открыть</a>", obj.slug)

    preview_link.short_description = "Превью"