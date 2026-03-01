"""
Utility functions for appointments application.

Currently contains helpers to query busy times for a given service and day.
"""

from __future__ import annotations

from datetime import date, datetime, time

from django.utils import timezone

from .models import Appointment


def get_busy_time_labels(service_id: int, day: date) -> set[str]:
    """
    Return a set of busy time labels ("HH:MM") for a service on a given day.

    Busy means there is an appointment in status NEW or CONFIRMED whose
    preferred_datetime falls within the day range in current timezone.

    Args:
        service_id: Service primary key.
        day: Date to check.

    Returns:
        Set of strings in format "HH:MM".
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
