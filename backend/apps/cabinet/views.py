"""
Представления приложения личного кабинета (cabinet).
Содержит:
- dashboard — главная страница с последними записями и результатами;
- appointments_view — список всех записей пользователя;
- results_view — список всех результатов исследований пользователя
  с автоматической отметкой непросмотренных как просмотренных.
"""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.results.models import ResearchResult


@login_required
def dashboard(request):
    """
    Главная страница личного кабинета.
    Отображает:
        - последние 5 записей пользователя;
        - последние 5 результатов исследований.
    Доступ:
        Требуется авторизация (login_required).
    """
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
    """
    Отображает список всех записей текущего пользователя.
    Сортировка:
        - по дате создания (новые сверху).
    Доступ:
        Требуется авторизация (login_required).
    """
    appointments = Appointment.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "cabinet/appointments.html", {"appointments": appointments})


@login_required
def results_view(request):
    """
    Отображает список всех результатов исследований пользователя.
    Побочный эффект:
        При открытии страницы все непросмотренные результаты
        (is_viewed=False) помечаются как просмотренные,
        а также устанавливается viewed_at.
    Сортировка:
        - по дате создания (новые сверху).
    Доступ:
        Требуется авторизация (login_required).
    """
    qs = ResearchResult.objects.filter(patient=request.user).order_by("-created_at")

    qs.filter(is_viewed=False).update(is_viewed=True, viewed_at=timezone.now())

    return render(request, "cabinet/results.html", {"results": qs})
