from django.shortcuts import get_object_or_404, render

from .models import Doctor


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
    return render(request, "staff/doctor_detail.html", {"doctor": doctor})