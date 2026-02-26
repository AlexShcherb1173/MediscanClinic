"""
Signals for results application.

Sends Telegram notification to patient's profile (if configured)
when a new ResearchResult is created.
"""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ResearchResult
from .telegram import send_telegram_message


@receiver(post_save, sender=ResearchResult)
def notify_new_result(sender, instance: ResearchResult, created: bool, **kwargs) -> None:
    """
    Notify patient via Telegram about newly uploaded research result.

    Requires:
        instance.patient.profile.telegram_chat_id to be set.
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