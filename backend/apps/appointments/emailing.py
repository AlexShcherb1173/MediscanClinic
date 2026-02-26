"""
Email notifications for appointment reminders.
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Appointment


def send_reminder_email(appt: Appointment, kind: str) -> None:
    """
    Send reminder email for an appointment.

    Args:
        appt: Appointment instance.
        kind: Reminder type: '24h' or '2h'.

    Notes:
        - If appointment has no email, function does nothing.
        - If DEFAULT_FROM_EMAIL is not set, function does nothing.
        - Uses fail_silently=True to avoid breaking reminder pipeline.
    """
    if not appt.email:
        return  # нет email — нечего слать

    when = timezone.localtime(appt.preferred_datetime).strftime("%d.%m.%Y %H:%M")
    service_name = appt.service.name if appt.service else "—"
    doctor_name = appt.doctor.full_name if appt.doctor else "—"
    human = "24 часа" if kind == "24h" else "2 часа"

    subject = f"Mediscan: напоминание о записи через {human}"
    body = "\n".join(
        [
            "Здравствуйте!",
            "",
            "Напоминаем о вашей записи в Mediscan.",
            f"Дата и время: {when}",
            f"Услуга: {service_name}",
            f"Врач: {doctor_name}",
            "",
            "Если нужно перенести запись — ответьте на это письмо или позвоните в клинику.",
            "",
            "Mediscan",
        ]
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not from_email:
        return

    clinic_copy = getattr(settings, "APPOINTMENTS_COPY_TO_EMAIL", "") or ""

    recipients = [appt.email]
    if clinic_copy:
        recipients.append(clinic_copy)

    send_mail(
        subject=subject,
        message=body,
        from_email=from_email,
        recipient_list=recipients,
        fail_silently=True,
    )