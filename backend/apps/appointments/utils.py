from __future__ import annotations

from datetime import date, datetime, time
from django.utils import timezone

from .models import Appointment


def get_busy_time_labels(service_id: int, day: date) -> set[str]:
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(day, time(0, 0)), tz)
    end = timezone.make_aware(datetime.combine(day, time(23, 59)), tz)

    qs = Appointment.objects.filter(
        service_id=service_id,
        preferred_datetime__gte=start,
        preferred_datetime__lte=end,
        status__in=[Appointment.Status.NEW, Appointment.Status.CONFIRMED],
    ).values_list("preferred_datetime", flat=True)

    return {timezone.localtime(dt).strftime("%H:%M") for dt in qs}