from __future__ import annotations

from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail

from .telegram_client import send_telegram_message

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.notifications.tasks import send_telegram_text_task
from .models import Appointment


@shared_task
def send_appointment_reminders() -> None:
    """
    Проверяем будущие записи и шлём напоминания:
    - за 24ч
    - за 2ч
    """
    now = timezone.now()

    # окно проверки на ближайшие 48 часов (чтобы не гонять базу слишком широко)
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

        # 24 часа: попадаем в окно 24ч ± 5 минут
        if (timedelta(hours=24) - timedelta(minutes=5)) <= delta <= (timedelta(hours=24) + timedelta(minutes=5)):
            if not appt.reminder_24h_sent:
                _send_and_mark(appt_id=appt.id, kind="24h")

        # 2 часа: окно 2ч ± 5 минут
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

        text = (
            "⏰ *Напоминание о записи*\n"
            f"*Когда:* {timezone.localtime(appt.preferred_datetime).strftime('%d.%m.%Y %H:%M')}\n"
            f"*Услуга:* {service_name}\n"
            f"*Врач:* {doctor_name}\n"
            f"*Пациент:* {appt.full_name}\n"
            f"*Телефон:* {appt.phone}\n"
            f"*Через:* {'24 часа' if kind=='24h' else '2 часа'}"
        )

        # ✅ Telegram async
        send_telegram_text_task.delay(text)

        # ✅ Email (sync) — можно тоже сделать async, если хочешь
        send_reminder_email(appt, kind)

        if kind == "24h":
            appt.reminder_24h_sent = True
        else:
            appt.reminder_2h_sent = True
        appt.save(update_fields=["reminder_24h_sent", "reminder_2h_sent"])

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_telegram_text_task(self, text: str) -> None:
    send_telegram_message(text)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_email_task(self, subject: str, body: str, to_email: str) -> None:
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not to_email:
        return
    send_mail(subject, body, from_email, [to_email], fail_silently=False)