"""
Celery-задачи и вспомогательные функции для приложения записей на приём.
Содержит:
- задачу отправки сообщений в Telegram;
- задачу отправки email (поддерживает разные форматы списка получателей);
- отправку SMS через sms.ru;
- планировщик напоминаний (окна ~24 часа / ~2 часа до приёма).
Примечание:
Часть helper-функций (normalize_emails, normalize_phone_for_smsru, smsru_send)
используется и в других модулях. В перспективе их лучше вынести в отдельный utils-модуль,
чтобы уменьшить связность и избежать циклических импортов.
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
    Приводит входное значение к списку email-адресов.
    Поддерживаемые форматы:
    - "a@b.com" (строка);
    - ["a@b.com", "c@d.com"] (list/tuple/set);
    - "['a@b.com']" (строка, содержащая сериализованный список);
    - ("a@b.com",) (кортеж).
    Правила:
    - пустые значения отбрасываются;
    - адреса приводятся к строке и обрезаются по краям.
    Параметры:
        value: Строка/коллекция/строка со списком.
    Возвращает:
        list[str]: Нормализованный список email-адресов (может быть пустым).
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
    Нормализует номер телефона под требования sms.ru.
    sms.ru обычно ожидает номер в виде набора цифр без '+' (например: 79XXXXXXXXX).
    Правила преобразования:
    - удаляются все нецифровые символы;
    - если получилось 11 цифр и номер начинается с '8', заменяет ведущую '8' на '7'.
    Параметры:
        phone (str): Номер телефона в произвольном формате.
    Возвращает:
        str: Номер телефона в формате digits-only для sms.ru (может быть пустой строкой,
             если из входа невозможно извлечь цифры).
    """
    digits = re.sub(r"\D+", "", phone or "")
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def smsru_send(to_phone: str, message: str) -> tuple[bool, str]:
    """
    Отправляет SMS через API sms.ru.
    Параметры:
        to_phone (str): Номер телефона получателя (сырой ввод).
        message (str): Текст сообщения.
    Возвращает:
        tuple[bool, str]:
            - (True, sms_id) — при успешной отправке;
            - (False, error_message) — при ошибке.
    Требования к настройкам:
        - SMS_RU_API_ID — обязателен.
        - SMS_SENDER — опционально (имя отправителя).
    Обработка ошибок:
        - при отсутствии SMS_RU_API_ID возвращает ошибку без запроса;
        - при пустом/некорректном номере возвращает ошибку;
        - при HTTP/JSON-ошибках возвращает текст ошибки;
        - при ошибке статуса sms.ru возвращает status_code/status_text.
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
        return (
            False,
            f"sms.ru error {payload.get('status_code')}: {payload.get('status_text')}",
        )

    sms_info = (payload.get("sms") or {}).get(to_norm) or {}
    if sms_info.get("status") != "OK":
        return (
            False,
            f"sms to {to_norm} error {sms_info.get('status_code')}: {sms_info.get('status_text')}",
        )

    return True, sms_info.get("sms_id", "OK")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_telegram_text_task(self, text: str) -> None:
    """
    Celery-задача: отправляет текстовое сообщение в Telegram.
    Поведение:
        - при ошибках задача автоматически ретраится (autoretry_for),
         с backoff и ограничением количества повторов.
    """
    send_telegram_message(text)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_email_task(self, subject: str, body: str, to_email) -> None:
    """
    Celery-задача: отправляет email.
    Получатели могут быть переданы в разных форматах (см. normalize_emails).
    Параметры:
        subject (str): Тема письма.
        body (str): Текст письма (plain text).
        to_email: Получатель(и): строка, список строк, кортеж, set или строка со списком.
    Правила:
        - from_email берётся из settings.DEFAULT_FROM_EMAIL;
        - если получателей нет — задача завершается без отправки;
        - fail_silently=False: при ошибке отправки будет исключение → ретрай Celery.
    """
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    recipients = normalize_emails(to_email)
    if not recipients:
        return

    send_mail(subject, body, from_email, recipients, fail_silently=False)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_sms_task(self, to_phone: str, message: str) -> None:
    """
    Celery-задача: отправляет SMS через sms.ru.
    Важно:
        - При ошибке провайдера выбрасывает исключение RuntimeError,
          чтобы Celery выполнил повторную попытку (retry).
    """
    ok, info = smsru_send(to_phone, message)
    if not ok:
        raise RuntimeError(info)


@shared_task
def send_appointment_reminders() -> None:
    """
    Планировщик напоминаний: сканирует ближайшие записи и отправляет напоминания.
    Окна отправки (с допуском ±5 минут):
        - примерно за 24 часа до приёма;
        - примерно за 2 часа до приёма.
    Каналы отправки:
        - Telegram;
        - Email;
        - SMS (только если настроен SMS_RU_API_ID).
    Примечания по производительности:
        - выбирает записи только в горизонте ближайших 48 часов;
        - использует select_related/only для уменьшения количества запросов.
    """
    now = timezone.now()
    until = now + timedelta(hours=48)

    qs = (
        Appointment.objects.filter(preferred_datetime__gt=now, preferred_datetime__lte=until)
        .select_related("service", "doctor")
        .only(
            "id",
            "full_name",
            "phone",
            "preferred_datetime",
            "reminder_24h_sent",
            "reminder_2h_sent",
            "service__name",
            "doctor__full_name",
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
    Отправляет напоминания по одной записи и выставляет флаг отправки.
    Работает в транзакции и блокирует строку записи (select_for_update),
    чтобы предотвратить двойную отправку при параллельном выполнении воркеров.
    Параметры:
        appt_id (int): ID записи (Appointment.id).
        kind (str): Тип окна напоминания: "24h" или "2h".
    Логика:
        1. Лочит запись в БД и повторно проверяет флаг reminder_*_sent.
        2. Формирует тексты для Telegram/Email/SMS.
        3. Ставит задачи Celery на отправку (delay).
        4. Отмечает соответствующий флаг (reminder_24h_sent или reminder_2h_sent)
           и сохраняет update_fields.
    Важно:
        Функция предполагает, что kind валиден ("24h"/"2h").
        При расширении логики стоит добавить явную валидацию kind.
    """
    with transaction.atomic():
        appt = Appointment.objects.select_for_update().select_related("service", "doctor").get(id=appt_id)

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
            f"Mediscan: напоминание. {dt_str}. " f"{service_name}. Врач: {doctor_name}. " f"До приема: {window_str}."
        )
        if getattr(settings, "SMS_RU_API_ID", ""):
            send_sms_task.delay(appt.phone, sms_text)

        if kind == "24h":
            appt.reminder_24h_sent = True
        else:
            appt.reminder_2h_sent = True

        appt.save(update_fields=["reminder_24h_sent", "reminder_2h_sent"])
