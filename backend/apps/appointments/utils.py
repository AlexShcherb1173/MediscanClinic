"""
Вспомогательные функции приложения записей на приём.
В текущей версии содержит утилиты для получения занятых временных слотов
по услуге и выбранной дате.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, cast

from django.utils import timezone

from .models import Appointment

normalize_phone_for_smsru = cast(Any, None)


def get_busy_time_labels(service_id: int, day: date) -> set[str]:
    """
    Возвращает набор занятых временных меток ("HH:MM")
    для указанной услуги и даты.
    Слот считается занятым, если существует запись (Appointment)
    со статусом NEW или CONFIRMED, у которой preferred_datetime
    попадает в диапазон выбранного дня с учётом текущей временной зоны.
    Параметры:
        service_id (int): ID услуги.
        day (date): Дата, для которой нужно определить занятость.
    Логика:
        - формируется диапазон [00:00:00; 23:59:59] выбранного дня;
        - диапазон делается timezone-aware;
        - выполняется фильтрация по услуге, статусу и времени;
        - возвращаются только временные метки в формате "HH:MM".
    Возвращает:
        set[str]: Набор строк вида "HH:MM" (например {"10:00", "10:30"}).
    """
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(day, time.min), tz)
    end = timezone.make_aware(datetime.combine(day, time.max), tz)

    qs = Appointment.objects.filter(
        service_id=service_id,
        preferred_datetime__gte=start,
        preferred_datetime__lte=end,
        status__in=[Appointment.Status.NEW, Appointment.Status.CONFIRMED],
    ).values_list("preferred_datetime", flat=True)

    return {timezone.localtime(dt, tz).strftime("%H:%M") for dt in qs}
