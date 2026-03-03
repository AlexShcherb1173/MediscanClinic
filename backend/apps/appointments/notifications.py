"""
Точки входа для отправки уведомлений по записям.
Предоставляет высокоуровневые функции для уведомления о:
- новой записи (email / Telegram),
- произвольном сообщении в Telegram.
Основной механизм отправки — Celery-задачи.
При недоступности Celery/Redis выполняется безопасный fallback
(синхронная отправка email или пропуск Telegram).
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
    DTO (payload) для уведомления о новой записи.
    Используется для передачи структурированных данных
    в email- и Telegram-уведомления.
    Поля:
        full_name: Полное имя пациента.
        phone: Телефон пациента.
        service_name: Название услуги.
        preferred_datetime_iso: Дата и время записи в формате ISO.
    """

    full_name: str
    phone: str
    service_name: str
    preferred_datetime_iso: str


def notify_email(payload: AppointmentNotification) -> None:
    """
    Отправляет email-уведомление о новой записи.
    Логика:
        1. Формирует тему и тело письма.
        2. Получает email получателя из настроек:
           - APPOINTMENTS_TO_EMAIL,
           - либо DEFAULT_FROM_EMAIL (fallback).
        3. Пытается отправить письмо через Celery-задачу.
        4. При ошибке (например, Celery/Redis недоступны)
           выполняет синхронную отправку через send_mail.
    Безопасность:
        - Если список получателей пустой — отправка не выполняется.
        - Используется fail_silently=True для fallback-отправки.
    Исключения:
        Исключения не пробрасываются наружу (логируются).
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
    Отправляет Telegram-уведомление о новой записи.
    Формирует текст сообщения в Markdown-формате
    и передаёт его в Celery-задачу send_telegram_text_task.
    Поведение при ошибке:
        - Если Celery/Redis недоступны, сообщение не отправляется.
        - Ошибка логируется, выполнение не прерывается.
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
    Отправляет произвольный текст в Telegram (best-effort).
    Используется для служебных уведомлений или отладочных сообщений.
    Поведение:
        - Отправка выполняется через Celery-задачу.
        - При недоступности очереди задача пропускается,
          ошибка логируется.
    """
    try:
        send_telegram_text_task.delay(text)
    except Exception as e:
        logger.exception("Celery/Redis unavailable, telegram skipped: %s", e)
