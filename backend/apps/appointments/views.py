from datetime import datetime

from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.services.models import Service
from .forms import AppointmentCreateForm, TIME_CHOICES
from .models import Appointment
from .notifications import AppointmentNotification, notify_email, notify_telegram
from .utils import get_busy_time_labels


def appointment_create(request):
    """
    Создание записи (без авторизации).
    GET: отображает форму (можно передать ?service=<id>)
    POST: сохраняет запись, отправляет уведомления, редирект на success
    """
    service_id = request.GET.get("service")
    service = get_object_or_404(Service, id=service_id, is_active=True) if service_id else None

    if request.method == "POST":
        # service можно передавать скрытым полем (на случай если GET пропал)
        service_id_post = request.POST.get("service_id") or service_id
        service = get_object_or_404(Service, id=service_id_post, is_active=True)

        form = AppointmentCreateForm(request.POST, service_id=service.id)
        if form.is_valid():
            appointment: Appointment = form.save(commit=False)
            appointment.service = service
            appointment.preferred_datetime = form.cleaned_data["preferred_datetime"]

            try:
                appointment.save()
            except IntegrityError:
                # В нашей форме сейчас ошибки у preferred_time, но оставим и preferred_datetime на всякий случай
                form.add_error(
                    "preferred_time",
                    "Этот слот уже занят. Выберите другое время.",
                )
            else:
                payload = AppointmentNotification(
                    full_name=appointment.full_name,
                    phone=appointment.phone,
                    service_name=appointment.service.name,
                    preferred_datetime_iso=appointment.preferred_datetime.isoformat(),
                )
                notify_email(payload)
                notify_telegram(payload)

                return redirect("appointments:success", pk=appointment.pk)
    else:
        # ВАЖНО: в GET тоже передаём service_id, чтобы форма могла подменять choices
        form = AppointmentCreateForm(service_id=service.id if service else None)

    return render(
        request,
        "appointments/create.html",
        {"form": form, "service": service},
    )


def appointment_success(request, pk: int):
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, "appointments/success.html", {"appointment": appointment})


def available_slots(request):
    """
    GET /appointments/slots/?service=<id>&date=YYYY-MM-DD
    Возвращает список свободных слотов по услуге и дате (занятые скрыты).
    """
    service_id = int(request.GET.get("service", "0") or 0)
    date_str = request.GET.get("date", "")

    if not service_id or not date_str:
        return JsonResponse({"slots": []})

    try:
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"slots": []})

    busy = get_busy_time_labels(service_id, day)
    slots = [{"value": v, "label": lbl} for (v, lbl) in TIME_CHOICES if v not in busy]
    return JsonResponse({"slots": slots})