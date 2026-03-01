"""
Views for cabinet application (personal account).

Provides:
- dashboard: last appointments and results
- appointments_view: all user appointments
- results_view: all user results + mark unread as viewed
"""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.results.models import ResearchResult


@login_required
def dashboard(request):
    """Cabinet dashboard page with last appointments and last results."""
    last_appointments = Appointment.objects.filter(user=request.user).order_by(
        "-created_at"
    )[:5]
    last_results = ResearchResult.objects.filter(patient=request.user).order_by(
        "-created_at"
    )[:5]

    return render(
        request,
        "cabinet/dashboard.html",
        {"last_appointments": last_appointments, "last_results": last_results},
    )


@login_required
def appointments_view(request):
    """List all appointments for the current user."""
    appointments = Appointment.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "cabinet/appointments.html", {"appointments": appointments})


@login_required
def results_view(request):
    """
    List all research results for the current user.

    Side effect:
        Marks unread results as viewed when opening the page.
    """
    qs = ResearchResult.objects.filter(patient=request.user).order_by("-created_at")

    qs.filter(is_viewed=False).update(is_viewed=True, viewed_at=timezone.now())

    return render(request, "cabinet/results.html", {"results": qs})
