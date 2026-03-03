"""
Вспомогательные функции приложения персонала (staff).
Содержит генератор временных слотов между двумя моментами времени
с фиксированным шагом.
"""

from __future__ import annotations

from datetime import datetime
from datetime import time as dt_time
from datetime import timedelta


def generate_time_slots(start: dt_time, end: dt_time, step_minutes: int = 30) -> list[dt_time]:
    """
    Генерирует список временных слотов между двумя значениями времени.
    Логика:
        - начальное время включается (start);
        - конечное время не включается (t < end);
        - шаг задаётся в минутах (step_minutes);
        - используется текущая дата только для вычисления шагов,
          в результате возвращаются объекты datetime.time.
    Параметры:
        start: Время начала интервала (включительно).
        end: Время окончания интервала (исключительно).
        step_minutes: Шаг в минутах (по умолчанию 30).
    Возвращает:
        list[datetime.time]: Список временных значений от start до end.
    Пример:
        generate_time_slots(09:00, 10:00, 30)
        → [09:00, 09:30]
    """
    slots: list[dt_time] = []
    cur = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)

    while cur < end_dt:
        slots.append(cur.time())
        cur += timedelta(minutes=step_minutes)

    return slots
