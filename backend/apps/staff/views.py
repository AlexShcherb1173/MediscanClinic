from django.shortcuts import get_object_or_404, render

from .models import Doctor, DoctorSchedule


def doctor_list(request):
    doctors = (
        Doctor.objects.filter(is_active=True)
        .prefetch_related("specialties")
        .order_by("full_name")
    )
    return render(request, "staff/doctor_list.html", {"doctors": doctors})


def doctor_detail(request, pk: int):
    doctor = get_object_or_404(
        Doctor.objects.filter(is_active=True).prefetch_related("specialties", "schedules"),
        pk=pk,
    )

    # Сгруппируем расписание по дням недели, чтобы красиво вывести
    weekday_map = dict(DoctorSchedule.WEEKDAYS)  # {0:"Понедельник",...}

    grouped = {}
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
        {
            "doctor": doctor,
            "schedules": schedules,  # ✅ теперь шаблон увидит schedules
        },
    )