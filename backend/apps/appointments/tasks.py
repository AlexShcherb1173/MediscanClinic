# apps/appointments/tasks.py
from __future__ import annotations

import re
from ast import literal_eval
from datetime import timedelta
from typing import Iterable

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Appointment
from .telegram_client import send_telegram_message


# ---------------- Email helpers ----------------
def normalize_emails(value) -> list[str]:
    """
    Нормализует значение с email(ами) в список строк.

    Поддерживает:
    - "a@b.com"
    - ["a@b.com", "c@d.com"]
    - "['a@b.com']"  (криво сериализованный список)
    - ("a@b.com",)
    """
    if not value:
        return []

    # уже коллекция
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for x in value:
            s = str(x).strip()
            if s:
                out.append(s)
        return out

    s = str(value).strip()
    if not s:
        return []

    # строка вида "['a@b.com']"
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = literal_eval(s)
            if isinstance(parsed, (list, tuple, set)):
                out: list[str] = []
                for x in parsed:
                    sx = str(x).strip()
                    if sx:
                        out.append(sx)
                return out
        except Exception:
            # если это невалидная строка-список — просто пойдём как одиночный адрес
            pass

    return [s]


# ---------------- SMS helpers ----------------
def normalize_phone_for_smsru(phone: str) -> str:
    """
    sms.ru обычно принимает номер в виде 79XXXXXXXXX без '+'.
    Приводим к цифрам и, если начинается с 8 и длина 11 — заменим на 7.
    """
    digits = re.sub(r"\D+", "", phone or "")
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def smsru_send(to_phone: str, message: str) -> tuple[bool, str]:
    """
    Возвращает (ok, info). info — текст ошибки или sms_id.
    """
    api_id = getattr(settings, "SMS_RU_API_ID", "") or ""
    if not api_id:
        return False, "SMS_RU_API_ID is empty"

    to_norm = normalize_phone_for_smsru(to_phone)
    if not to_norm:
        return False, "Empty phone"

    url = "https://sms.ru/sms/send"
    data = {
        "api_id": api_id,
        "to": to_norm,
        "msg": message,
        "json": 1,
    }

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


# ---------------- Tasks ----------------
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_telegram_text_task(self, text: str) -> None:
    send_telegram_message(text)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_email_task(self, subject: str, body: str, to_email) -> None:
    """
    to_email может быть:
    - str
    - list[str]
    - "['a@b.com']" (строка)
    """
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    recipients = normalize_emails(to_email)
    if not recipients:
        return

    send_mail(subject, body, from_email, recipients, fail_silently=False)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_sms_task(self, to_phone: str, message: str) -> None:
    ok, info = smsru_send(to_phone, message)
    if not ok:
        raise RuntimeError(info)


@shared_task
def send_appointment_reminders() -> None:
    """
    Проверяем будущие записи и шлём напоминания:
    - за 24ч
    - за 2ч
    Каналы: Telegram + Email + SMS (sms.ru)
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

        # -------- Telegram --------
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

        # -------- Email --------
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
            # можно передавать как исходное значение, но лучше уже список
            send_email_task.delay(subject, body, recipients)

        # -------- SMS --------
        sms_text = (
            f"Mediscan: напоминание. {dt_str}. "
            f"{service_name}. Врач: {doctor_name}. "
            f"До приема: {window_str}."
        )
        if getattr(settings, "SMS_RU_API_ID", ""):
            send_sms_task.delay(appt.phone, sms_text)

        # mark sent
        if kind == "24h":
            appt.reminder_24h_sent = True
        else:
            appt.reminder_2h_sent = True

        appt.save(update_fields=["reminder_24h_sent", "reminder_2h_sent"])