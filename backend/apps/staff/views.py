"""
Views for staff application.

Provides:
- doctor_list: list of active doctors
- doctor_detail: doctor profile with grouped weekly schedule
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404, render

from .models import Doctor, DoctorSchedule


def doctor_list(request):
    """
    Display list of active doctors.

    Prefetches specialties for efficient rendering.
    """
    doctors = (
        Doctor.objects.filter(is_active=True)
        .prefetch_related("specialties")
        .order_by("full_name")
    )
    return render(request, "staff/doctor_list.html", {"doctors": doctors})


def doctor_detail(request, pk: int):
    """
    Display doctor detail page with grouped schedule by weekday.

    Args:
        pk: Doctor primary key.

    Context:
        doctor: Doctor instance
        schedules: list[dict] like:
            [{"weekday": 0, "weekday_label": "Понедельник", "windows": [{"from": "09:00", "to": "13:00"}]}]
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
