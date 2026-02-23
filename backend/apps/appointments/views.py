from __future__ import annotations

import calendar
from datetime import date as dt_date, timedelta, datetime, time

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET

from apps.promos.models import Promo
from apps.services.models import Service
from apps.staff.models import Doctor

from .forms import AppointmentCreateForm
from .models import Appointment, AppointmentSlot
from .notifications import AppointmentNotification, notify_email, notify_telegram


# ---------------- Helpers ----------------
def _safe_day(value: str | None) -> dt_date | None:
    if not value:
        return None
    return parse_date(value)


def _first_day_with_slots(service_id: int | None, start_day: dt_date, days_ahead: int = 31) -> dt_date | None:
    qs = AppointmentSlot.objects.filter(
        is_active=True,
        is_booked=False,
        starts_at__date__gte=start_day,
        starts_at__date__lte=start_day + timedelta(days=days_ahead),
    )
    if service_id:
        qs = qs.filter(service_id=service_id)
    return qs.order_by("starts_at").values_list("starts_at__date", flat=True).first()


# -------- Calendar (month grid) --------
@require_GET
def calendar_view(request):
    today = timezone.localdate()

    m = request.GET.get("m")  # "2026-02"
    selected_raw = request.GET.get("preferred_date") or request.GET.get("date") or ""
    selected_date = _safe_day(selected_raw) or today

    if m:
        try:
            year, month = map(int, m.split("-"))
            first = dt_date(year, month, 1)
        except Exception:
            first = dt_date(selected_date.year, selected_date.month, 1)
    else:
        first = dt_date(selected_date.year, selected_date.month, 1)

    year, month = first.year, first.month
    _, days_in_month = calendar.monthrange(year, month)
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


@require_GET
def slots(request):
    service_id = (
        request.GET.get("service")
        or request.GET.get("service_id")
        or request.GET.get("service-select")
        or ""
    )
    date_str = request.GET.get("preferred_date") or request.GET.get("date") or ""
    day = parse_date(date_str)

    # ✅ читаем ФИО и телефон (придут из hx-include)
    full_name = (request.GET.get("full_name") or request.GET.get("id_full_name") or "").strip()
    phone = (request.GET.get("phone") or request.GET.get("id_phone") or "").strip()
    patient_ready = (len(full_name) >= 3) and (len(phone) >= 6)

    service_selected = bool(service_id)
    date_selected = bool(day)

    # ✅ если пациент не готов — не показываем слоты, а только подсказку
    if not patient_ready:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": False,
                "service_selected": False,
                "date_selected": False,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    # услуга не выбрана
    if not service_selected:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": True,
                "service_selected": False,
                "date_selected": False,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    # услуга выбрана, но дата ещё нет
    if not date_selected:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": True,
                "service_selected": True,
                "date_selected": False,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    tz = timezone.get_current_timezone()
    start_local = timezone.make_aware(datetime.combine(day, time.min), tz)
    end_local = timezone.make_aware(datetime.combine(day, time.max), tz)

    qs = AppointmentSlot.objects.filter(
        is_active=True,
        is_booked=False,
        starts_at__gte=start_local,
        starts_at__lte=end_local,
        service_id=service_id,
    ).order_by("starts_at")

    slot_items = [
        {"id": str(slot.pk), "label": timezone.localtime(slot.starts_at, tz).strftime("%H:%M")}
        for slot in qs
    ]

    selected_slot_id = (
        request.GET.get("slot")
        or request.GET.get("selected_slot")
        or request.GET.get("slot_id")
        or ""
    )

    return render(
        request,
        "appointments/_slots_tiles.html",
        {
            "patient_ready": True,
            "service_selected": True,
            "date_selected": True,
            "slot_items": slot_items,
            "selected_slot_id": str(selected_slot_id),
        },
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

        if not service_id and promo_services_qs.count() == 1:
            service_id = str(promo_services_qs.first().id)
            locked_service = True

    service = (
        get_object_or_404(Service, id=service_id, is_active=True, category__is_active=True)
        if service_id else None
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
            slot_obj: AppointmentSlot = form.cleaned_data["slot"]

            try:
                with transaction.atomic():
                    slot_locked = AppointmentSlot.objects.select_for_update().get(pk=slot_obj.pk)

                    if (not slot_locked.is_active) or slot_locked.is_booked:
                        form.add_error("slot", "Этот слот только что заняли. Выберите другое время.")
                        return render(request, "appointments/create.html", {**base_ctx, "form": form})

                    slot_locked.is_booked = True
                    slot_locked.save(update_fields=["is_booked"])

                    appointment: Appointment = form.save(commit=False)

                    # ✅ привязка к пользователю (если авторизован)
                    appointment.user = request.user if request.user.is_authenticated else None

                    appointment.slot = slot_locked
                    appointment.service = slot_locked.service
                    appointment.doctor = doctor
                    appointment.promo = promo
                    appointment.preferred_datetime = slot_locked.starts_at
                    appointment.save()

            except (IntegrityError, AppointmentSlot.DoesNotExist):
                form.add_error("slot", "Этот слот только что заняли. Выберите другое время.")
                return render(request, "appointments/create.html", {**base_ctx, "form": form})

            payload = AppointmentNotification(
                full_name=appointment.full_name,
                phone=appointment.phone,
                service_name=appointment.service.name if appointment.service else "",
                preferred_datetime_iso=appointment.preferred_datetime.isoformat() if appointment.preferred_datetime else "",
            )
            notify_email(payload)
            notify_telegram(payload)

            request.session.pop("appointment_draft", None)
            return redirect("appointments:success", pk=appointment.pk)

    else:
        # ВАЖНО: дату подставляем только если услуга уже выбрана (чтобы placeholder даты был виден)
        initial = {
            "full_name": draft.get("full_name", ""),
            "phone": draft.get("phone", ""),
            "email": draft.get("email", ""),
            "comment": draft.get("comment", ""),
        }

        if service:
            init_day = _safe_day(draft.get("preferred_date")) or timezone.localdate()
            nearest = _first_day_with_slots(service.id, init_day, days_ahead=31)
            if nearest:
                init_day = nearest
            initial["preferred_date"] = init_day

        form = AppointmentCreateForm(
            service_id=service.id if service else None,
            doctor_id=doctor.id if doctor else None,
            lock_service=locked_service,
            lock_doctor=locked_doctor,
            service_queryset=promo_services_qs if promo_services_qs is not None else None,
            initial=initial,
        )

    return render(request, "appointments/create.html", {**base_ctx, "form": form})


def appointment_success(request, pk: int):
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, "appointments/success.html", {"appointment": appointment})