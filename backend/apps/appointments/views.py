from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.services.models import Service
from apps.staff.models import Doctor
from apps.promos.models import Promo

from .forms import AppointmentCreateForm
from .models import Appointment, AppointmentSlot
from .notifications import AppointmentNotification, notify_email, notify_telegram


# ---------- calendar (для виджета дат/HTMX) ----------
@require_GET
def calendar_view(request):
    service_id = request.GET.get("service")
    today = timezone.localdate()
    days = [today + timedelta(days=i) for i in range(0, 21)]  # 3 недели

    return render(
        request,
        "appointments/_calendar.html",
        {
            "days": days,
            "selected": request.GET.get("date") or str(today),
            "service_id": service_id,
        },
    )


# ---------- HTMX: slot options (HTML <option>...) ----------
@require_GET
def slots(request):
    service_id = request.GET.get("service")
    date_str = request.GET.get("date")  # YYYY-MM-DD

    qs = AppointmentSlot.objects.filter(is_active=True, is_booked=False)

    if service_id:
        qs = qs.filter(service_id=service_id)

    if date_str:
        qs = qs.filter(starts_at__date=date_str)

    qs = qs.order_by("starts_at")

    return render(request, "appointments/_slot_options.html", {"slots": qs})


# ---------- create appointment ----------
def appointment_create(request):
    service_id = request.GET.get("service")
    doctor_id = request.GET.get("doctor")
    promo_slug = request.GET.get("promo")

    locked_service = bool(service_id)
    locked_doctor = bool(doctor_id)

    next_url = request.GET.get("next")
    if next_url:
        request.session["services_return_url"] = next_url

    promo = None
    promo_services_qs = None

    if promo_slug:
        promo = get_object_or_404(Promo, slug=promo_slug, is_active=True)
        promo_services_qs = promo.services.filter(is_active=True, category__is_active=True)

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

    if request.method == "POST":
        # service/doctor/promo можно передавать скрытыми полями
        service_id_post = request.POST.get("service") or service_id
        doctor_id_post = request.POST.get("doctor") or doctor_id
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
            service_queryset=promo_services_qs if promo_services_qs is not None else None,
        )

        if form.is_valid():
            slot = form.cleaned_data["slot"]

            try:
                with transaction.atomic():
                    # ✅ блокировка слота от гонок
                    slot_locked = AppointmentSlot.objects.select_for_update().get(pk=slot.pk)
                    if slot_locked.is_booked or not slot_locked.is_active:
                        raise ValidationError("Этот слот только что заняли. Выберите другое время.")

                    slot_locked.is_booked = True
                    slot_locked.save(update_fields=["is_booked"])

                    appointment: Appointment = form.save(commit=False)
                    appointment.slot = slot_locked
                    appointment.service = service or slot_locked.service
                    appointment.doctor = doctor
                    appointment.promo = promo
                    appointment.preferred_datetime = slot_locked.starts_at
                    appointment.save()

            except ValidationError as e:
                form.add_error("slot", str(e))
            except IntegrityError:
                form.add_error("slot", "На это время уже есть запись. Выберите другое время.")
            else:
                payload = AppointmentNotification(
                    full_name=appointment.full_name,
                    phone=appointment.phone,
                    service_name=appointment.service.name if appointment.service else "",
                    preferred_datetime_iso=appointment.preferred_datetime.isoformat()
                    if appointment.preferred_datetime else "",
                )
                notify_email(payload)
                notify_telegram(payload)

                request.session.pop("services_return_url", None)
                return redirect("appointments:success", pk=appointment.pk)

    else:
        form = AppointmentCreateForm(
            service_id=service.id if service else None,
            doctor_id=doctor.id if doctor else None,
            lock_service=locked_service,
            lock_doctor=locked_doctor,
            service_queryset=promo_services_qs if promo_services_qs is not None else None,
            initial={
                "preferred_date": timezone.localdate(),
            },
        )

    return render(
        request,
        "appointments/create.html",
        {
            "form": form,
            "service": service,
            "doctor": doctor,
            "promo": promo,
            "locked_service": locked_service,
            "locked_doctor": locked_doctor,
        },
    )


def appointment_success(request, pk: int):
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, "appointments/success.html", {"appointment": appointment})