"""
Notification entrypoints for appointments.

Provides high-level functions to notify about:
- new appointment (email/telegram)
- arbitrary telegram text

Primary channel uses Celery tasks; falls back gracefully if Celery/Redis unavailable.
"""

import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail

from .tasks import normalize_emails, send_email_task, send_telegram_text_task

logger = logging.getLogger("appointments")


@dataclass(frozen=True)
class AppointmentNotification:
    """
    Notification payload for new appointment.

    Attributes:
        full_name: Patient full name.
        phone: Patient phone.
        service_name: Service name.
        preferred_datetime_iso: ISO datetime string for appointment time.
    """

    full_name: str
    phone: str
    service_name: str
    preferred_datetime_iso: str


def notify_email(payload: AppointmentNotification) -> None:
    """
    Notify clinic by email about a new appointment.

    Uses Celery task; falls back to synchronous send_mail if task queue is unavailable.
    """
    subject = "Mediscan: новая запись"
    body = (
        f"Имя: {payload.full_name}\n"
        f"Телефон: {payload.phone}\n"
        f"Услуга: {payload.service_name}\n"
        f"Дата/время: {payload.preferred_datetime_iso}\n"
    )

    to_email = getattr(settings, "APPOINTMENTS_TO_EMAIL", "") or getattr(
        settings, "DEFAULT_FROM_EMAIL", ""
    )
    recipients = normalize_emails(to_email)
    if not recipients:
        return

    try:
        send_email_task.delay(subject, body, recipients)
    except Exception as e:
        logger.exception("Celery/Redis unavailable, sending email sync: %s", e)
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        send_mail(subject, body, from_email, recipients, fail_silently=True)


def notify_telegram(payload: AppointmentNotification) -> None:
    """
    Notify clinic by Telegram about a new appointment.
    """
    text = (
        "🩺 *Новая запись*\n"
        f"*Имя:* {payload.full_name}\n"
        f"*Телефон:* {payload.phone}\n"
        f"*Услуга:* {payload.service_name}\n"
        f"*Дата/время:* {payload.preferred_datetime_iso}\n"
    )
    try:
        send_telegram_text_task.delay(text)
    except Exception as e:
        logger.exception("Celery/Redis unavailable, telegram skipped: %s", e)


def notify_telegram_text(text: str) -> None:
    """
    Send arbitrary text to Telegram (best-effort, via Celery task).
    """
    try:
        send_telegram_text_task.delay(text)
    except Exception as e:
        logger.exception("Celery/Redis unavailable, telegram skipped: %s", e)
