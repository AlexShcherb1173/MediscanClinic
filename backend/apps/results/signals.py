"""
Сигналы приложения результатов (results).
Отправляет уведомление в Telegram пациенту
при создании нового ResearchResult.
"""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ResearchResult
from .telegram import send_telegram_message


@receiver(post_save, sender=ResearchResult)
def notify_new_result(sender, instance: ResearchResult, created: bool, **kwargs) -> None:
    """
    Обработчик сигнала post_save для модели ResearchResult.
    Логика:
        - срабатывает только при создании нового объекта (created=True);
        - проверяет наличие профиля пациента;
        - проверяет наличие telegram_chat_id в профиле;
        - отправляет уведомление в Telegram.
    Требования:
        - у пользователя должен существовать profile;
        - profile.telegram_chat_id должен быть заполнен.
    Параметры:
        sender: модель-источник сигнала (ResearchResult).
        instance: созданный объект результата исследования.
        created: флаг создания (True только при первом сохранении).
        **kwargs: дополнительные аргументы сигнала Django.
    """
    if not created:
        return

    profile = getattr(instance.patient, "profile", None)
    chat_id = getattr(profile, "telegram_chat_id", "") if profile else ""
    if not chat_id:
        return

    text = (
        "✅ Mediscan: загружен новый результат исследования.\n"
        f"📄 {instance.title}\n"
        "Откройте личный кабинет → Результаты."
    )
    send_telegram_message(chat_id, text)
