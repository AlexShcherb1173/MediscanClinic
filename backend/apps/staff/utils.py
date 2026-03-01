"""
Utility helpers for staff application.

Currently contains generator for time slots between two times with a fixed step.
"""

from __future__ import annotations

from datetime import datetime
from datetime import time as dt_time
from datetime import timedelta


def generate_time_slots(
    start: dt_time, end: dt_time, step_minutes: int = 30
) -> list[dt_time]:
    """
    Generate time slots between start and end using a fixed step.

    Uses today's date only to calculate stepping; returns time objects.

    Args:
        start: start time (inclusive).
        end: end time (exclusive).
        step_minutes: step in minutes.

    Returns:
        List of times (datetime.time) from start to end (t < end).
    """
    slots: list[dt_time] = []
    cur = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)

    while cur < end_dt:
        slots.append(cur.time())
        cur += timedelta(minutes=step_minutes)

    return slots
