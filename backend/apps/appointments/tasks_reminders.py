"""
Celery-задача отправки напоминаний о записях на приём.
Модуль реализует отправку напоминаний по окнам времени:
- примерно за 24 часа до приёма (с допуском ± заданное окно),
- примерно за 2 часа до приёма (с допуском ± заданное окно).
Каналы отправки:
- Telegram (через Celery-задачу send_telegram_text_task),
- Email (через Celery-задачу send_email_task).
Алгоритм защищён от дублей при параллельном выполнении воркеров
за счёт блокировки строк select_for_update(skip_locked=True).
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
    Находит ближайшие записи и отправляет напоминания, если они ещё не были отправлены.
    Для каждого окна (24h, 2h):
        1) вычисляет интервал времени [target - window; target + window];
        2) в транзакции лочит подходящие записи через select_for_update(skip_locked=True),
           чтобы разные воркеры не обработали одну и ту же запись одновременно;
        3) отправляет напоминания в Telegram и/или по Email через отдельные Celery-задачи;
        4) выставляет флаги reminder_telegram_sent / reminder_email_sent;
        5) записывает reminded_at и сохраняет только изменённые поля.
    Учитываемые записи:
        - preferred_datetime попадает в интервал окна;
        - статус записи: NEW или CONFIRMED.
    Возвращает:
        int: количество отправок напоминаний (считается по каналам:
             Telegram и Email инкрементируют счётчик независимо).
    Примечания:
        - Если APPOINTMENTS_TO_EMAIL и DEFAULT_FROM_EMAIL не заданы, email-канал пропускается.
        - Время форматируется в локальной временной зоне.
    """
    now = timezone.now()

    windows = [
        ("24h", now + timedelta(hours=24), 30),  # +/- 30 min
        ("2h", now + timedelta(hours=2), 20),  # +/- 20 min
    ]

    total = 0

    for label, target, minutes in windows:
        start = target - timedelta(minutes=minutes)
        end = target + timedelta(minutes=minutes)

        with transaction.atomic():
            qs = (
                Appointment.objects.select_for_update(skip_locked=True)
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
                    to_email = getattr(settings, "APPOINTMENTS_TO_EMAIL", "") or getattr(
                        settings, "DEFAULT_FROM_EMAIL", ""
                    )
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
