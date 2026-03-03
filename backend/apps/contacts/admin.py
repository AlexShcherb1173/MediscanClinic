"""
Конфигурация Django Admin для приложения контактов (contacts).
Позволяет отправлять объекты AdminTelegramMessage в Telegram:
- через массовое действие "send_to_telegram";
- автоматически при сохранении объекта в админке.
"""

from __future__ import annotations

from django.contrib import admin, messages
from django.utils import timezone

from .models import AdminTelegramMessage
from .telegram import send_telegram_message


@admin.action(description="Отправить выбранные сообщения в Telegram")
def send_to_telegram(modeladmin, request, queryset):
    """
    Массово отправляет выбранные сообщения в Telegram.
    Логика:
        - обрабатываются только сообщения с is_sent=False;
        - при успешной отправке выставляются флаги is_sent=True и sent_at;
        - при ошибке выводится сообщение через django.contrib.messages.
    В интерфейсе админки отображается количество успешных отправок и ошибок.
    """
    ok, fail = 0, 0

    for obj in queryset:
        if obj.is_sent:
            continue
        try:
            send_telegram_message(obj.text)
            obj.is_sent = True
            obj.sent_at = timezone.now()
            obj.save(update_fields=["is_sent", "sent_at"])
            ok += 1
        except Exception as e:
            fail += 1
            messages.error(request, f"Ошибка отправки #{obj.pk}: {e}")

    if ok:
        messages.success(request, f"Отправлено: {ok}")
    if fail:
        messages.warning(request, f"Ошибок: {fail}")


@admin.register(AdminTelegramMessage)
class AdminTelegramMessageAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели AdminTelegramMessage.
    Возможности:
        - отображение статуса отправки и дат;
        - фильтрация по статусу и дате создания;
        - поиск по тексту сообщения;
        - массовая отправка сообщений в Telegram.
    """

    list_display = ("id", "is_sent", "created_at", "sent_at")
    list_filter = ("is_sent", "created_at")
    search_fields = ("text",)
    actions = [send_to_telegram]

    def save_model(self, request, obj, form, change):
        """
        Автоматически отправляет сообщение в Telegram после сохранения в админке.
        Поведение:
            - если сообщение уже отправлено (is_sent=True), повторная отправка не выполняется;
            - при успешной отправке обновляются поля is_sent и sent_at;
            - при ошибке отправки сообщение остаётся неотправленным,
              а пользователю показывается уведомление об ошибке.
        """
        super().save_model(request, obj, form, change)

        if obj.is_sent:
            return

        try:
            send_telegram_message(obj.text)
            obj.is_sent = True
            obj.sent_at = timezone.now()
            obj.save(update_fields=["is_sent", "sent_at"])
            messages.success(request, "Сообщение отправлено в Telegram ✅")
        except Exception as e:
            messages.error(request, f"Не удалось отправить в Telegram: {e}")
