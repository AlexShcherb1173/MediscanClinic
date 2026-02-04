from datetime import datetime, timedelta, time as dtime

from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.services.models import Service
from apps.staff.models import Doctor, DoctorSchedule
from apps.promos.models import Promo  # ✅

from .forms import AppointmentCreateForm
from .models import Appointment
from .notifications import AppointmentNotification, notify_email, notify_telegram


# ======= slots helpers =======
def generate_default_slots() -> list[dtime]:
    """
    Стандартные слоты по услуге (если врач не выбран).
    Каждые 20 минут 08:00–20:40.
    """
    start = dtime(8, 0)
    end = dtime(20, 40)
    step = timedelta(minutes=20)

    slots: list[dtime] = []
    current = datetime.combine(timezone.localdate(), start)

    while current.time() <= end:
        slots.append(current.time())
        current += step

    return slots


# ======= create appointment =======
def appointment_create(request):
    service_id = request.GET.get("service")
    doctor_id = request.GET.get("doctor")
    promo_slug = request.GET.get("promo")  # ✅

    locked_service = bool(service_id)
    locked_doctor = bool(doctor_id)

    # ✅ если пришли с next — запоминаем, чтобы "Изменить услугу" вернуло назад
    next_url = request.GET.get("next")
    if next_url:
        request.session["services_return_url"] = next_url

    promo = None
    promo_services_qs = None

    # ✅ контекст "акция"
    if promo_slug:
        promo = get_object_or_404(Promo, slug=promo_slug, is_active=True)
        promo_services_qs = promo.services.filter(is_active=True, category__is_active=True)

        # если service не передали явно, а по акции 1 услуга — подставим и зафиксируем
        if not service_id and promo_services_qs.exists() and promo_services_qs.count() == 1:
            service_id = str(promo_services_qs.first().id)
            locked_service = True

    service = (
        get_object_or_404(Service, id=service_id, is_active=True, category__is_active=True)
        if service_id else None
    )
    doctor = (
        get_object_or_404(Doctor, id=doctor_id, is_active=True)
        if doctor_id else None
    )

    draft = request.session.get("appointment_draft", {})

    if request.method == "POST":
        # ✅ кнопка "Изменить услугу/врача": сохраняем черновик и уходим назад
        if request.POST.get("_action") == "change_service":
            request.session["appointment_draft"] = {
                "full_name": request.POST.get("full_name", ""),
                "phone": request.POST.get("phone", ""),
                "comment": request.POST.get("comment", ""),
                "preferred_date": request.POST.get("preferred_date", ""),
                "preferred_time": request.POST.get("preferred_time", ""),
            }

            return_url = request.session.get("services_return_url")
            if return_url:
                return redirect(return_url)
            return redirect("services:list")

        # service/doctor/promo можно передавать скрытыми полями
        service_id_post = request.POST.get("service_id") or request.POST.get("service") or service_id
        doctor_id_post = request.POST.get("doctor_id") or request.POST.get("doctor") or doctor_id
        promo_slug_post = request.POST.get("promo") or promo_slug

        promo = (
            get_object_or_404(Promo, slug=promo_slug_post, is_active=True)
            if promo_slug_post else None
        )
        promo_services_qs = (
            promo.services.filter(is_active=True, category__is_active=True)
            if promo else None
        )

        service = (
            get_object_or_404(Service, id=service_id_post, is_active=True, category__is_active=True)
            if service_id_post else None
        )
        doctor = (
            get_object_or_404(Doctor, id=doctor_id_post, is_active=True)
            if doctor_id_post else None
        )

        form = AppointmentCreateForm(
            request.POST,
            service_id=service.id if service else None,
            doctor_id=doctor.id if doctor else None,
            lock_service=locked_service,
            lock_doctor=locked_doctor,
            service_queryset=promo_services_qs if promo_services_qs is not None else None,  # ✅ ограничение услуг
        )

        if form.is_valid():
            appointment: Appointment = form.save(commit=False)

            appointment.service = service
            appointment.doctor = doctor
            appointment.promo = promo  # ✅ сохраняем акцию (может быть None)
            appointment.preferred_datetime = form.cleaned_data["preferred_datetime"]

            try:
                appointment.save()
            except IntegrityError:
                form.add_error("preferred_time", "На это время уже есть запись. Выберите другое время.")
            else:
                payload = AppointmentNotification(
                    full_name=appointment.full_name,
                    phone=appointment.phone,
                    service_name=appointment.service.name if appointment.service else "",
                    preferred_datetime_iso=appointment.preferred_datetime.isoformat(),
                )
                notify_email(payload)
                notify_telegram(payload)

                request.session.pop("appointment_draft", None)
                request.session.pop("services_return_url", None)

                return redirect("appointments:success", pk=appointment.pk)

    else:
        form = AppointmentCreateForm(
            service_id=service.id if service else None,
            doctor_id=doctor.id if doctor else None,
            lock_service=locked_service,
            lock_doctor=locked_doctor,
            service_queryset=promo_services_qs if promo_services_qs is not None else None,  # ✅ ограничение услуг
            initial={
                "full_name": draft.get("full_name", ""),
                "phone": draft.get("phone", ""),
                "comment": draft.get("comment", ""),
                "preferred_date": draft.get("preferred_date", ""),
                "preferred_time": draft.get("preferred_time", ""),
            },
        )

    return render(
        request,
        "appointments/create.html",
        {
            "form": form,
            "service": service,
            "doctor": doctor,
            "promo": promo,  # ✅
            "locked_service": locked_service,
            "locked_doctor": locked_doctor,
        },
    )


# ======= slots API (doctor first, fallback to service default) =======
@require_GET
def appointment_slots(request):
    """
    GET /appointments/slots/?date=YYYY-MM-DD&doctor=<id>&service=<id>
    """
    date_str = request.GET.get("date")
    service_id = request.GET.get("service")
    doctor_id = request.GET.get("doctor")

    if not date_str:
        return JsonResponse({"slots": []})

    try:
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"slots": []})

    # --- 1) строим слоты ---
    if doctor_id:
        schedules = DoctorSchedule.objects.filter(
            doctor_id=doctor_id,
            weekday=day.weekday(),
        )

        slots: list[dtime] = []
        step = timedelta(minutes=20)

        for s in schedules:
            current = datetime.combine(day, s.time_from)
            end = datetime.combine(day, s.time_to)
            while current < end:
                slots.append(current.time())
                current += step
    else:
        slots = generate_default_slots()

    # --- 2) занятые ---
    taken_qs = Appointment.objects.filter(preferred_datetime__date=day)

    if doctor_id:
        taken_qs = taken_qs.filter(doctor_id=doctor_id)
    elif service_id:
        taken_qs = taken_qs.filter(service_id=service_id)

    taken_times = {dt.time() for dt in taken_qs.values_list("preferred_datetime", flat=True)}

    # --- 3) отдаём в JSON ---
    result = [
        {
            "value": t.strftime("%H:%M"),
            "label": t.strftime("%H:%M"),
            "available": t not in taken_times,
        }
        for t in slots
    ]

    return JsonResponse({"slots": result})


def appointment_success(request, pk: int):
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, "appointments/success.html", {"appointment": appointment})