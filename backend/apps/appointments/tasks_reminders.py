"""
Celery task for sending appointment reminders.

This module implements a time-window based reminder sender:
- about 24 hours before appointment (+/- window)
- about 2 hours before appointment (+/- window)

Channels:
- Telegram (via Celery task)
- Email (via Celery task)
"""

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Appointment
from .tasks import send_email_task, send_telegram_text_task


@shared_task
def send_appointments_reminders() -> int:
    """
    Find upcoming appointments and send reminders if not sent yet.

    For each configured window (24h, 2h):
    - locks rows with select_for_update(skip_locked=True) inside a transaction
    - sends Telegram/email using Celery tasks
    - marks reminder flags and reminded_at

    Returns:
        int: number of reminder sends (counts per-channel).
    """
    now = timezone.now()

    windows = [
        ("24h", now + timedelta(hours=24), 30),  # +/- 30 min
        ("2h", now + timedelta(hours=2), 20),    # +/- 20 min
    ]

    total = 0

    for label, target, minutes in windows:
        start = target - timedelta(minutes=minutes)
        end = target + timedelta(minutes=minutes)

        with transaction.atomic():
            qs = (
                Appointment.objects
                .select_for_update(skip_locked=True)
                .filter(preferred_datetime__gte=start, preferred_datetime__lte=end)
                .filter(status__in=[Appointment.Status.NEW, Appointment.Status.CONFIRMED])
                .select_related("service")
            )

            for appt in qs:
                service_name = appt.service.name if appt.service else "—"
                dt_str = timezone.localtime(appt.preferred_datetime).strftime("%d.%m.%Y %H:%M")

                if not appt.reminder_telegram_sent:
                    text = (
                        "⏰ *Напоминание о записи*\n"
                        f"*Имя:* {appt.full_name}\n"
                        f"*Телефон:* {appt.phone}\n"
                        f"*Услуга:* {service_name}\n"
                        f"*Когда:* {dt_str}\n"
                        f"*Окно:* {label}\n"
                    )
                    send_telegram_text_task.delay(text)
                    appt.reminder_telegram_sent = True
                    total += 1

                if not appt.reminder_email_sent:
                    to_email = getattr(settings, "APPOINTMENTS_TO_EMAIL", "") or getattr(settings, "DEFAULT_FROM_EMAIL", "")
                    if to_email:
                        subject = f"Mediscan: напоминание о записи ({label})"
                        body = (
                            f"Имя: {appt.full_name}\n"
                            f"Телефон: {appt.phone}\n"
                            f"Услуга: {service_name}\n"
                            f"Когда: {dt_str}\n"
                        )
                        send_email_task.delay(subject, body, to_email)
                        appt.reminder_email_sent = True
                        total += 1

                if appt.reminder_email_sent or appt.reminder_telegram_sent:
                    appt.reminded_at = timezone.now()
                    appt.save(
                        update_fields=[
                            "reminder_email_sent",
                            "reminder_telegram_sent",
                            "reminded_at",
                        ]
                    )

    return total