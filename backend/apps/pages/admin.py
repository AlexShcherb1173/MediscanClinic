"""
Конфигурация Django Admin для приложения страниц (pages).
Предоставляет административный интерфейс для управления
статическими CMS-страницами, включая:
- автогенерацию slug;
- управление публикацией;
- ссылку предпросмотра на фронтенд.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Page.
    Возможности:
        - автоматическое заполнение slug из title;
        - фильтрация по статусу публикации;
        - поиск по заголовку, slug и HTML-контенту;
        - ссылка «Превью» для открытия страницы на фронтенде.
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

    @admin.display(description="Превью")
    def preview_link(self, obj: Page):
        """
        Генерирует ссылку предпросмотра страницы на фронтенде.
        Использует slug-ориентированную маршрутизацию:
            /page/<slug>/
        Возвращает:
            HTML-ссылку с target="_blank" или "-" если slug отсутствует.
        """
        if not obj.slug:
            return "-"

        return format_html(
            "<a href='/page/{}/' target='_blank'>Открыть</a>",
            obj.slug,
        )
