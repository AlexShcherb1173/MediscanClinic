import logging
from dataclasses import dataclass
from django.conf import settings

from .tasks import send_telegram_text_task, send_email_task

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
    if to_email:
        send_email_task.delay(subject, body, to_email)


def notify_telegram(payload: AppointmentNotification) -> None:
    text = (
        "🩺 *Новая запись*\n"
        f"*Имя:* {payload.full_name}\n"
        f"*Телефон:* {payload.phone}\n"
        f"*Услуга:* {payload.service_name}\n"
        f"*Дата/время:* {payload.preferred_datetime_iso}\n"
    )
    send_telegram_text_task.delay(text)


def notify_telegram_text(text: str) -> None:
    send_telegram_text_task.delay(text)