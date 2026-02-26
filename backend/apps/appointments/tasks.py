"""
Celery tasks and helper functions for appointments.

Includes:
- Telegram sending task
- Email sending task (supports multiple recipient formats)
- SMS sending via sms.ru
- Reminder scheduler logic (24h / 2h)

Note:
Some helper functions here (normalize_emails, smsru_send) are also used by other modules.
Consider moving them into a separate utils module later to avoid circular coupling.
"""

from __future__ import annotations

import re
from ast import literal_eval
from datetime import timedelta

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Appointment
from .telegram_client import send_telegram_message


def normalize_emails(value) -> list[str]:
    """
    Normalize an input value into list of email strings.

    Supports:
    - "a@b.com"
    - ["a@b.com", "c@d.com"]
    - "['a@b.com']"  (stringified list)
    - ("a@b.com",)
    """
    if not value:
        return []

    if isinstance(value, (list, tuple, set)):
        return [str(x).strip() for x in value if str(x).strip()]

    s = str(value).strip()
    if not s:
        return []

    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = literal_eval(s)
            if isinstance(parsed, (list, tuple, set)):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass

    return [s]


def normalize_phone_for_smsru(phone: str) -> str:
    """
    Normalize phone number for sms.ru.

    sms.ru commonly expects number as 79XXXXXXXXX (digits only).
    Converts:
    - keeps digits
    - if 11 digits and starts with 8 -> replaces leading 8 with 7
    """
    digits = re.sub(r"\D+", "", phone or "")
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def smsru_send(to_phone: str, message: str) -> tuple[bool, str]:
    """
    Send SMS via sms.ru API.

    Returns:
        (True, sms_id) on success
        (False, error_message) on failure
    """
    api_id = getattr(settings, "SMS_RU_API_ID", "") or ""
    if not api_id:
        return False, "SMS_RU_API_ID is empty"

    to_norm = normalize_phone_for_smsru(to_phone)
    if not to_norm:
        return False, "Empty phone"

    url = "https://sms.ru/sms/send"
    data = {"api_id": api_id, "to": to_norm, "msg": message, "json": 1}

    sender = getattr(settings, "SMS_SENDER", "") or ""
    if sender:
        data["from"] = sender

    try:
        r = requests.post(url, data=data, timeout=15)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        return False, f"HTTP/JSON error: {e}"

    if payload.get("status") != "OK":
        return False, f"sms.ru error {payload.get('status_code')}: {payload.get('status_text')}"

    sms_info = (payload.get("sms") or {}).get(to_norm) or {}
    if sms_info.get("status") != "OK":
        return False, f"sms to {to_norm} error {sms_info.get('status_code')}: {sms_info.get('status_text')}"

    return True, sms_info.get("sms_id", "OK")


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_telegram_text_task(self, text: str) -> None:
    """Celery task: send text message to Telegram."""
    send_telegram_message(text)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_email_task(self, subject: str, body: str, to_email) -> None:
    """
    Celery task: send email.

    Args:
        subject: email subject
        body: email plain-text body
        to_email: str or list[str] or stringified list
    """
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    recipients = normalize_emails(to_email)
    if not recipients:
        return

    send_mail(subject, body, from_email, recipients, fail_silently=False)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_sms_task(self, to_phone: str, message: str) -> None:
    """Celery task: send SMS (raises to retry if provider returns error)."""
    ok, info = smsru_send(to_phone, message)
    if not ok:
        raise RuntimeError(info)


@shared_task
def send_appointment_reminders() -> None:
    """
    Scan upcoming appointments and send reminders:
    - ~24 hours before
    - ~2 hours before

    Channels:
    - Telegram
    - Email
    - SMS (if SMS_RU_API_ID configured)
    """
    now = timezone.now()
    until = now + timedelta(hours=48)

    qs = (
        Appointment.objects
        .filter(preferred_datetime__gt=now, preferred_datetime__lte=until)
        .select_related("service", "doctor")
        .only(
            "id", "full_name", "phone", "preferred_datetime",
            "reminder_24h_sent", "reminder_2h_sent",
            "service__name", "doctor__full_name",
        )
    )

    for appt in qs:
        dt = appt.preferred_datetime
        delta = dt - now

        if (timedelta(hours=24) - timedelta(minutes=5)) <= delta <= (timedelta(hours=24) + timedelta(minutes=5)):
            if not appt.reminder_24h_sent:
                _send_and_mark(appt_id=appt.id, kind="24h")

        if (timedelta(hours=2) - timedelta(minutes=5)) <= delta <= (timedelta(hours=2) + timedelta(minutes=5)):
            if not appt.reminder_2h_sent:
                _send_and_mark(appt_id=appt.id, kind="2h")


def _send_and_mark(appt_id: int, kind: str) -> None:
    """
    Send reminders for a single appointment and mark the corresponding flag.

    Runs inside transaction with row lock to prevent duplicate sends.
    """
    with transaction.atomic():
        appt = (
            Appointment.objects
            .select_for_update()
            .select_related("service", "doctor")
            .get(id=appt_id)
        )

        if kind == "24h" and appt.reminder_24h_sent:
            return
        if kind == "2h" and appt.reminder_2h_sent:
            return

        service_name = appt.service.name if appt.service else "—"
        doctor_name = appt.doctor.full_name if appt.doctor else "—"
        dt_local = timezone.localtime(appt.preferred_datetime)
        dt_str = dt_local.strftime("%d.%m.%Y %H:%M")
        window_str = "24 часа" if kind == "24h" else "2 часа"

        tg_text = (
            "⏰ *Напоминание о записи*\n"
            f"*Когда:* {dt_str}\n"
            f"*Услуга:* {service_name}\n"
            f"*Врач:* {doctor_name}\n"
            f"*Пациент:* {appt.full_name}\n"
            f"*Телефон:* {appt.phone}\n"
            f"*Через:* {window_str}"
        )
        send_telegram_text_task.delay(tg_text)

        to_email = getattr(settings, "APPOINTMENTS_TO_EMAIL", "") or getattr(settings, "DEFAULT_FROM_EMAIL", "")
        recipients = normalize_emails(to_email)
        if recipients:
            subject = f"Mediscan: напоминание о записи ({window_str})"
            body = (
                f"Имя: {appt.full_name}\n"
                f"Телефон: {appt.phone}\n"
                f"Услуга: {service_name}\n"
                f"Врач: {doctor_name}\n"
                f"Когда: {dt_str}\n"
                f"Окно: {window_str}\n"
            )
            send_email_task.delay(subject, body, recipients)

        sms_text = (
            f"Mediscan: напоминание. {dt_str}. "
            f"{service_name}. Врач: {doctor_name}. "
            f"До приема: {window_str}."
        )
        if getattr(settings, "SMS_RU_API_ID", ""):
            send_sms_task.delay(appt.phone, sms_text)

        if kind == "24h":
            appt.reminder_24h_sent = True
        else:
            appt.reminder_2h_sent = True

        appt.save(update_fields=["reminder_24h_sent", "reminder_2h_sent"])