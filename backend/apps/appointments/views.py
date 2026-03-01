"""
Views for appointments application.

Includes:
- calendar_view: renders month grid (partial)
- slots: returns available slots tiles (partial for HTMX)
- appointment_create: create booking with transaction-safe slot locking
- appointment_success: success page (should be access-protected)

Also contains helper functions for parsing dates/ints and user auto-fill.
"""

from __future__ import annotations

import calendar
from datetime import date as dt_date, datetime, time, timedelta

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


def appointments_index(request):
    """
    Simple index redirect for appointments section.
    """
    return redirect("appointments:create")


# ---------------- Helpers ----------------
def _safe_int(value: str | None) -> int | None:
    """
    Convert string to int safely. Returns None for invalid values.
    """
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_day(value: str | None) -> dt_date | None:
    """
    Parse a YYYY-MM-DD string into a date. Returns None for invalid values.
    """
    if not value:
        return None
    return parse_date(value)


def _first_day_with_slots(service_id: int | None, start_day: dt_date, days_ahead: int = 31) -> dt_date | None:
    """
    Find the nearest date (starting from start_day) that has free active slots.

    Args:
        service_id: optional service filter
        start_day: starting date for search
        days_ahead: look-ahead window

    Returns:
        date of the first available slot or None
    """
    qs = AppointmentSlot.objects.filter(
        is_active=True,
        is_booked=False,
        starts_at__date__gte=start_day,
        starts_at__date__lte=start_day + timedelta(days=days_ahead),
    )
    if service_id:
        qs = qs.filter(service_id=service_id)
    return qs.order_by("starts_at").values_list("starts_at__date", flat=True).first()


def _user_full_name(user) -> str:
    """
    Get user's full name from various possible sources.

    Strategy:
    1) user.get_full_name()
    2) user.full_name
    3) related objects: profile/patient/person (full_name or fio)
    4) last Appointment.full_name for that user
    5) fallback: email or username
    """
    if not user or not getattr(user, "is_authenticated", False):
        return ""

    try:
        full = (user.get_full_name() or "").strip()
        if full:
            return full
    except Exception:
        pass

    full = (getattr(user, "full_name", "") or "").strip()
    if full:
        return full

    for rel in ("profile", "patient", "person"):
        obj = getattr(user, rel, None)
        if obj is not None:
            full = (getattr(obj, "full_name", "") or getattr(obj, "fio", "") or "").strip()
            if full:
                return full

    last = (
        Appointment.objects.filter(user=user)
        .exclude(full_name__isnull=True)
        .exclude(full_name__exact="")
        .order_by("-created_at", "-id")
        .first()
    )
    if last:
        return (last.full_name or "").strip()

    email = (getattr(user, "email", "") or "").strip()
    if email:
        return email
    return (getattr(user, "username", "") or "").strip()


def _user_phone(user) -> str:
    """
    Get user's phone from user or related profile objects.

    Strategy:
    1) user.phone
    2) related profile/patient/person phone
    3) last Appointment.phone for that user
    """
    if not user or not getattr(user, "is_authenticated", False):
        return ""

    phone = (getattr(user, "phone", "") or "").strip()
    if phone:
        return phone

    for rel in ("profile", "patient", "person"):
        obj = getattr(user, rel, None)
        if obj is not None:
            phone = (getattr(obj, "phone", "") or "").strip()
            if phone:
                return phone

    last = (
        Appointment.objects.filter(user=user)
        .exclude(phone__isnull=True)
        .exclude(phone__exact="")
        .order_by("-created_at", "-id")
        .first()
    )
    if last:
        return (last.phone or "").strip()

    return ""


# -------- Calendar (month grid) --------
@require_GET
def calendar_view(request):
    """
    Render month grid partial for appointment date selection.

    Query params:
        m: month in format YYYY-MM (optional)
        preferred_date/date: selected day (YYYY-MM-DD)
    """
    today = timezone.localdate()

    m = request.GET.get("m")  # "2026-02"
    selected_raw = request.GET.get("preferred_date") or request.GET.get("date") or ""
    selected_date = _safe_day(selected_raw)

    # ✅ если пришла прошедшая дата — принудительно ставим today
    if not selected_date or selected_date < today:
        selected_date = today

    # определяем первый день отображаемого месяца
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

    # ✅ запрещаем уход в прошлые месяцы
    min_month = today.replace(day=1)
    prev_disabled = prev_month < min_month

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
            "prev_disabled": prev_disabled,
        },
    )


@require_GET
def slots(request):
    """
    Render available time slots (HTMX partial).

    Requires "patient_ready" (full_name + phone) and selected service/date.
    """
    service_id_raw = (
        request.GET.get("service")
        or request.GET.get("service_id")
        or request.GET.get("service-select")
        or ""
    )
    service_id = _safe_int(service_id_raw)

    date_str = (request.GET.get("preferred_date") or request.GET.get("date") or "").strip()
    day = parse_date(date_str) if date_str else None

    full_name = (request.GET.get("full_name") or request.GET.get("id_full_name") or "").strip()
    phone = (request.GET.get("phone") or request.GET.get("id_phone") or "").strip()
    patient_ready = (len(full_name) >= 3) and (len(phone) >= 6)

    service_selected = bool(service_id)
    date_selected = (day is not None)

    # ✅ запрет прошлого на сервере (если кто-то подставит вручную)
    today = timezone.localdate()
    date_in_past = bool(day) and (day < today)

    if not patient_ready:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": False,
                "service_selected": False,
                "date_selected": False,
                "date_in_past": False,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    if not service_selected:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": True,
                "service_selected": False,
                "date_selected": False,
                "date_in_past": False,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    if not date_selected:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": True,
                "service_selected": True,
                "date_selected": False,
                "date_in_past": False,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    # если дата выбрана, но в прошлом
    if date_in_past:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": True,
                "service_selected": True,
                "date_selected": True,
                "date_in_past": True,
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
            "date_in_past": False,
            "slot_items": slot_items,
            "selected_slot_id": str(selected_slot_id),
        },
    )


def appointment_create(request):
    """
    Create an appointment.

    Supports optional locking via query params:
        service=<id>   -> lock service field
        doctor=<id>    -> lock doctor field
        promo=<slug>   -> restrict services to promo.services

    Uses transaction + select_for_update() to prevent double booking:
    - locks slot row
    - checks active/not booked
    - marks slot as booked
    - creates Appointment record
    - sends notifications (email + telegram)
    """
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

    draft = request.session.get("appointment_draft", {}) or {}

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
                    slot_day = timezone.localtime(slot_obj.starts_at).date()
                    if slot_day < timezone.localdate():
                        form.add_error("slot", "Нельзя записаться на прошедшую дату.")
                        return render(request, "appointments/create.html", {**base_ctx, "form": form})

                    if (not slot_locked.is_active) or slot_locked.is_booked:
                        form.add_error("slot", "Этот слот уже занят. Выберите другой.")
                        return render(request, "appointments/create.html", {**base_ctx, "form": form})

                    slot_locked.is_booked = True
                    slot_locked.save(update_fields=["is_booked"])

                    appointment: Appointment = form.save(commit=False)
                    appointment.user = request.user if request.user.is_authenticated else None

                    appointment.slot = slot_locked
                    appointment.service = slot_locked.service
                    appointment.doctor = doctor
                    appointment.promo = promo
                    appointment.preferred_datetime = slot_locked.starts_at
                    appointment.save()

            except (IntegrityError, AppointmentSlot.DoesNotExist):
                form.add_error("slot", "Этот слот уже занят. Выберите другой.")
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
            # store last pk for anonymous access to success page
            request.session["last_appointment_pk"] = appointment.pk
            request.session.save()

            return redirect("appointments:success", pk=appointment.pk)

    else:
        user_full_name = _user_full_name(request.user)
        user_phone = _user_phone(request.user)
        user_email = (getattr(request.user, "email", "") or "").strip() if request.user.is_authenticated else ""

        initial = {
            "full_name": draft.get("full_name") or user_full_name or "",
            "phone": draft.get("phone") or user_phone or "",
            "email": draft.get("email") or user_email or "",
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
    """
    Render appointment success page.

    Security:
    - Authenticated users can view only their own appointments.
    - Anonymous users can view only the last appointment created in this session.
    """
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.user.is_authenticated:
        if appointment.user_id != request.user.id:
            return redirect("appointments:create")
    else:
        if request.session.get("last_appointment_pk") != appointment.pk:
            return redirect("appointments:create")

    return render(request, "appointments/success.html", {"appointment": appointment})