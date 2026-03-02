"""
Представления приложения персонала (staff).
Реализует:
- список активных врачей;
- детальную страницу врача с отображением
  сгруппированного по дням недели расписания.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404, render

from .models import Doctor, DoctorSchedule


def doctor_list(request):
    """
    Отображает список активных врачей.
    Логика:
        - выбираются только врачи с is_active=True;
        - выполняется prefetch_related("specialties") для
          оптимизации количества SQL-запросов;
        - сортировка по ФИО.
    Параметры:
        request: HttpRequest текущего запроса.
    Возвращает:
        HttpResponse со страницей списка врачей.
    """
    doctors = (
        Doctor.objects.filter(is_active=True)
        .prefetch_related("specialties")
        .order_by("full_name")
    )
    return render(request, "staff/doctor_list.html", {"doctors": doctors})


def doctor_detail(request, pk: int):
    """
    Отображает детальную страницу врача.
    Загружает врача по первичному ключу (pk) и формирует
    сгруппированное расписание по дням недели.
    Логика:
        - врач должен быть активным;
        - подгружаются специализации и расписания;
        - расписания группируются по weekday;
        - интервалы времени форматируются в строку "HH:MM".
    Параметры:
        request: HttpRequest текущего запроса.
        pk: Первичный ключ врача.
    Контекст шаблона:
        doctor: объект Doctor.
        schedules: список словарей вида:
            [
                {
                    "weekday": 0,
                    "weekday_label": "Понедельник",
                    "windows": [
                        {"from": "09:00", "to": "13:00"},
                        ...
                    ]
                },
                ...
            ]
    Возвращает:
        HttpResponse со страницей профиля врача.
    """
    doctor = get_object_or_404(
        Doctor.objects.filter(is_active=True).prefetch_related(
            "specialties", "schedules"
        ),
        pk=pk,
    )

    weekday_map = dict(DoctorSchedule.WEEKDAYS)

    grouped: dict[int, list[DoctorSchedule]] = {}
    for s in doctor.schedules.all().order_by("weekday", "time_from"):
        grouped.setdefault(s.weekday, []).append(s)

    schedules = []
    for weekday in sorted(grouped.keys()):
        windows = [
            {
                "from": sch.time_from.strftime("%H:%M"),
                "to": sch.time_to.strftime("%H:%M"),
            }
            for sch in grouped[weekday]
        ]
        schedules.append(
            {
                "weekday": weekday,
                "weekday_label": weekday_map.get(weekday, str(weekday)),
                "windows": windows,
            }
        )

    return render(
        request,
        "staff/doctor_detail.html",
        {"doctor": doctor, "schedules": schedules},
    )
