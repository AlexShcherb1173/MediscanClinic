from __future__ import annotations

import calendar
from datetime import timedelta, date as dt_date

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.promos.models import Promo
from apps.services.models import Service
from apps.staff.models import Doctor

from .forms import AppointmentCreateForm
from .models import Appointment, AppointmentSlot
from .notifications import AppointmentNotification, notify_email, notify_telegram


# -------- Calendar (month grid) --------
@require_GET
def calendar_view(request):
    """
    HTMX partial calendar (month grid)
    GET /appointments/calendar/?m=YYYY-MM&preferred_date=YYYY-MM-DD
    """
    today = timezone.localdate()

    m = request.GET.get("m")  # "2026-02"
    selected_raw = request.GET.get("preferred_date") or request.GET.get("date")

    # selected -> date
    if selected_raw:
        try:
            selected_date = dt_date.fromisoformat(selected_raw)
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    # month anchor
    if m:
        try:
            year, month = map(int, m.split("-"))
            first = dt_date(year, month, 1)
        except Exception:
            first = dt_date(selected_date.year, selected_date.month, 1)
    else:
        first = dt_date(selected_date.year, selected_date.month, 1)

    year, month = first.year, first.month
    _, days_in_month = calendar.monthrange(year, month)  # weekday Monday=0..Sunday=6
    first_weekday = first.weekday()

    blanks = list(range(first_weekday))
    days = [dt_date(year, month, d) for d in range(1, days_in_month + 1)]

    prev_month = (first.replace(day=1) - timedelta(days=1)).replace(day=1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)

    return render(
        request,
        "appointments/_calendar_month.html",
        {
            "today": today,
            "selected": selected_date.strftime("%Y-%m-%d"),
            "year": year,
            "month": month,
            "blanks": blanks,
            "days": days,
            "prev_m": prev_month.strftime("%Y-%m"),
            "next_m": next_month.strftime("%Y-%m"),
        },
    )


# -------- HTMX: slot options --------
@require_GET
def slots(request):
    service_id = (
        request.GET.get("service")
        or request.GET.get("service-select")
        or request.GET.get("service_id")
        or ""
    )
    date_str = request.GET.get("preferred_date") or request.GET.get("date") or ""

    qs = AppointmentSlot.objects.filter(is_active=True, is_booked=False)

    if service_id:
        qs = qs.filter(service_id=service_id)

    # ✅ безопасный парсинг даты
    day = parse_date(date_str)  # понимает только YYYY-MM-DD
    if day:
        qs = qs.filter(starts_at__date=day)

    qs = qs.order_by("starts_at")

    selected_slot = request.GET.get("selected_slot") or ""
    return render(
        request,
        "appointments/_slot_options.html",
        {"slots": qs, "selected_slot": selected_slot},
    )


# -------- Create appointment --------
def appointment_create(request):
    service_id = request.GET.get("service")
    doctor_id = request.GET.get("doctor")
    promo_slug = request.GET.get("promo")

    locked_service = bool(service_id)
    locked_doctor = bool(doctor_id)

    promo = None
    promo_services_qs = None

    if promo_slug:
        promo = get_object_or_404(Promo, slug=promo_slug, is_active=True)
        promo_services_qs = promo.services.filter(is_active=True, category__is_active=True)

        # если по акции только 1 услуга — подставим и зафиксируем
        if not service_id and promo_services_qs.count() == 1:
            service_id = str(promo_services_qs.first().id)
            locked_service = True

    service = (
        get_object_or_404(Service, id=service_id, is_active=True, category__is_active=True)
        if service_id
        else None
    )
    doctor = get_object_or_404(Doctor, id=doctor_id, is_active=True) if doctor_id else None

    draft = request.session.get("appointment_draft", {})

    base_ctx = {
        "service": service,
        "doctor": doctor,
        "promo": promo,
        "locked_service": locked_service,
        "locked_doctor": locked_doctor,
    }

    if request.method == "POST":
        form = AppointmentCreateForm(
            request.POST,
            service_id=service.id if service else None,
            doctor_id=doctor.id if doctor else None,
            lock_service=locked_service,
            lock_doctor=locked_doctor,
            service_queryset=promo_services_qs if promo_services_qs is not None else None,
        )

        if form.is_valid():
            slot: AppointmentSlot = form.cleaned_data["slot"]

            # ✅ атомарно бронируем слот
            try:
                with transaction.atomic():
                    slot_locked = AppointmentSlot.objects.select_for_update().get(pk=slot.pk)

                    if (not slot_locked.is_active) or slot_locked.is_booked:
                        form.add_error("slot", "Этот слот только что заняли. Выберите другое время.")
                        return render(request, "appointments/create.html", {**base_ctx, "form": form})

                    slot_locked.is_booked = True
                    slot_locked.save(update_fields=["is_booked"])

                    appointment: Appointment = form.save(commit=False)
                    appointment.slot = slot_locked
                    appointment.service = slot_locked.service  # источник истины
                    appointment.doctor = doctor
                    appointment.promo = promo
                    appointment.preferred_datetime = slot_locked.starts_at

                    appointment.save()

            except IntegrityError:
                # на случай если есть constraint, который сработал на save()
                form.add_error("slot", "Этот слот только что заняли. Выберите другое время.")
                return render(request, "appointments/create.html", {**base_ctx, "form": form})

            # уведомления
            payload = AppointmentNotification(
                full_name=appointment.full_name,
                phone=appointment.phone,
                service_name=appointment.service.name if appointment.service else "",
                preferred_datetime_iso=appointment.preferred_datetime.isoformat()
                if appointment.preferred_datetime
                else "",
            )
            notify_email(payload)
            notify_telegram(payload)

            request.session.pop("appointment_draft", None)
            return redirect("appointments:success", pk=appointment.pk)

    else:
        # дефолтная дата = сегодня
        init_date = draft.get("preferred_date")
        if init_date:
            try:
                init_date = dt_date.fromisoformat(init_date)
            except ValueError:
                init_date = timezone.localdate()
        else:
            init_date = timezone.localdate()

        form = AppointmentCreateForm(
            service_id=service.id if service else None,
            doctor_id=doctor.id if doctor else None,
            lock_service=locked_service,
            lock_doctor=locked_doctor,
            service_queryset=promo_services_qs if promo_services_qs is not None else None,
            initial={
                "full_name": draft.get("full_name", ""),
                "phone": draft.get("phone", ""),
                "email": draft.get("email", ""),
                "comment": draft.get("comment", ""),
                "preferred_date": init_date,  # ✅ date object
            },
        )

    return render(request, "appointments/create.html", {**base_ctx, "form": form})


def appointment_success(request, pk: int):
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, "appointments/success.html", {"appointment": appointment})