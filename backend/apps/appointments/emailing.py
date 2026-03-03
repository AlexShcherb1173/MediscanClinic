"""
Модуль отправки email-уведомлений для напоминаний о записи.
Содержит функции для формирования и отправки писем пациентам
о предстоящем приёме (за 24 часа или за 2 часа до визита).
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Appointment


def send_reminder_email(appt: Appointment, kind: str) -> None:
    """
    Отправляет email-напоминание о предстоящей записи.
    Формирует тему и текст письма с информацией о:
    - дате и времени приёма,
    - выбранной услуге,
    - враче.
    Поддерживаются два типа напоминаний:
    - "24h" — за 24 часа до приёма;
    - "2h" — за 2 часа до приёма.
    Письмо отправляется пациенту, а также (опционально)
    на служебный email клиники, если он указан в настройках.
    Параметры:
        appt (Appointment): Экземпляр записи на приём.
        kind (str): Тип напоминания ("24h" или "2h").
    Логика работы:
        1. Если у записи отсутствует email пациента — отправка не выполняется.
        2. Если в настройках не задан DEFAULT_FROM_EMAIL — отправка не выполняется.
        3. Время приёма приводится к локальной временной зоне.
        4. Используется fail_silently=True, чтобы ошибка отправки
           не прерывала выполнение фоновой задачи (например Celery).
    Исключения:
        Исключения не пробрасываются наружу (fail_silently=True).
    Возвращаемое значение:
        None
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
