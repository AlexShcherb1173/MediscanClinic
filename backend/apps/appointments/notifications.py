# apps/appointments/notifications.py
import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail

from .tasks import send_telegram_text_task, send_email_task, normalize_emails

logger = logging.getLogger("appointments")


@dataclass(frozen=True)
class AppointmentNotification:
    full_name: str
    phone: str
    service_name: str
    preferred_datetime_iso: str


def notify_email(payload: AppointmentNotification) -> None:
    subject = "Mediscan: новая запись"
    body = (
        f"Имя: {payload.full_name}\n"
        f"Телефон: {payload.phone}\n"
        f"Услуга: {payload.service_name}\n"
        f"Дата/время: {payload.preferred_datetime_iso}\n"
    )

    to_email = getattr(settings, "APPOINTMENTS_TO_EMAIL", "") or getattr(settings, "DEFAULT_FROM_EMAIL", "")
    recipients = normalize_emails(to_email)
    if not recipients:
        return

    try:
        # передаём recipients (list[str]) — и в таске это тоже ок
        send_email_task.delay(subject, body, recipients)
    except Exception as e:
        # fallback: не ломаем запись
        logger.exception("Celery/Redis unavailable, sending email sync: %s", e)
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        send_mail(subject, body, from_email, recipients, fail_silently=True)


def notify_telegram(payload: AppointmentNotification) -> None:
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
    try:
        send_telegram_text_task.delay(text)
    except Exception as e:
        logger.exception("Celery/Redis unavailable, telegram skipped: %s", e)