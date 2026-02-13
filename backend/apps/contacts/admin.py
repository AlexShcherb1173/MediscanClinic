from django.contrib import admin, messages
from django.utils import timezone

from .models import AdminTelegramMessage
from .telegram import send_telegram_message


@admin.action(description="Отправить выбранные сообщения в Telegram")
def send_to_telegram(modeladmin, request, queryset):
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
    list_display = ("id", "is_sent", "created_at", "sent_at")
    list_filter = ("is_sent", "created_at")
    search_fields = ("text",)
    actions = [send_to_telegram]

    # ✅ авто-отправка при сохранении в админке
    def save_model(self, request, obj, form, change):
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
