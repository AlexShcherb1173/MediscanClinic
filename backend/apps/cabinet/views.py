from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.results.models import ResearchResult


@login_required
def dashboard(request):
    last_appointments = (
        Appointment.objects.filter(user=request.user)
        .order_by("-created_at")[:5]
    )

    last_results = (
        ResearchResult.objects.filter(patient=request.user)
        .order_by("-created_at")[:5]
    )

    return render(request, "cabinet/dashboard.html", {
        "last_appointments": last_appointments,
        "last_results": last_results,
    })


@login_required
def appointments_view(request):
    appointments = (
        Appointment.objects.filter(user=request.user)
        .order_by("-created_at")
    )

    return render(request, "cabinet/appointments.html", {
        "appointments": appointments
    })


@login_required
def results_view(request):
    qs = ResearchResult.objects.filter(
        patient=request.user
    ).order_by("-created_at")

    # ⭐ помечаем как просмотренные при заходе на страницу
    qs.filter(is_viewed=False).update(
        is_viewed=True,
        viewed_at=timezone.now()
    )

    return render(request, "cabinet/results.html", {
        "results": qs
    })