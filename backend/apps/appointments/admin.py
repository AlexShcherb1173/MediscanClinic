"""
Admin configuration for appointments.

Provides:
- Appointment listing with confirm/cancel buttons
- doctor calendar view in admin
- row highlighting based on status and datetime
"""

from datetime import datetime, time, timedelta

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import format_html

from apps.staff.models import Doctor

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Appointment model.

    Includes custom actions:
    - confirm/cancel via inline buttons
    - doctor daily calendar view
    """

    class Media:
        css = {"all": ("admin/admin.css",)}

    list_display = (
        "preferred_datetime",
        "full_name",
        "service",
        "doctor",
        "status",
        "action_buttons",
    )
    list_filter = ("status", "service", "doctor")
    date_hierarchy = "preferred_datetime"
    ordering = ("preferred_datetime",)

    def get_urls(self):
        """Register custom admin URLs for calendar and status actions."""
        urls = super().get_urls()
        custom = [
            path(
                "calendar/",
                self.admin_site.admin_view(self.calendar_view),
                name="appointments-calendar",
            ),
            path(
                "<int:pk>/confirm/",
                self.admin_site.admin_view(self.confirm_appointment),
                name="appointment-confirm",
            ),
            path(
                "<int:pk>/cancel/",
                self.admin_site.admin_view(self.cancel_appointment),
                name="appointment-cancel",
            ),
        ]
        return custom + urls

    def action_buttons(self, obj):
        """Render confirm/cancel buttons in list view."""
        return format_html(
            "<a class='button' href='{}/confirm/'>✔ Confirm</a>&nbsp;"
            "<a class='button' style='color:#b91c1c' href='{}/cancel/'>✖ Cancel</a>",
            obj.pk,
            obj.pk,
        )

    action_buttons.short_description = "Действия"

    def confirm_appointment(self, request, pk):
        """Set appointment status to CONFIRMED."""
        obj = Appointment.objects.get(pk=pk)
        obj.status = Appointment.Status.CONFIRMED
        obj.save(update_fields=["status"])
        messages.success(request, "Запись подтверждена")
        return redirect("..")

    def cancel_appointment(self, request, pk):
        """Set appointment status to CANCELED."""
        obj = Appointment.objects.get(pk=pk)
        obj.status = Appointment.Status.CANCELED
        obj.save(update_fields=["status"])
        messages.warning(request, "Запись отменена")
        return redirect("..")

    def get_queryset(self, request):
        """
        Attach `row_class` attribute for template row highlighting.

        Note:
            This iterates over queryset items. For very large datasets this may be heavy,
            but it's acceptable for typical admin use.
        """
        qs = super().get_queryset(request)
        now = timezone.now()

        for obj in qs:
            if (
                obj.preferred_datetime
                and obj.preferred_datetime < now
                and obj.status == Appointment.Status.CONFIRMED
            ):
                obj.row_class = "status-completed"
            else:
                obj.row_class = f"status-{obj.status}"

        return qs

    def calendar_view(self, request):
        """
        Render doctor daily calendar with 20-min slots.

        Query params:
            doctor: doctor id
            date: YYYY-MM-DD
        """
        doctor_id = request.GET.get("doctor")
        date_str = request.GET.get("date")

        day = parse_date(date_str) if date_str else timezone.localdate()
        if not day:
            day = timezone.localdate()

        doctors = Doctor.objects.filter(is_active=True).order_by("full_name")
        doctor = doctors.filter(pk=doctor_id).first() if doctor_id else doctors.first()

        start_time = time(8, 0)
        end_time = time(20, 40)
        step = timedelta(minutes=20)

        slots = []
        current = datetime.combine(day, start_time)
        end_dt = datetime.combine(day, end_time)
        while current <= end_dt:
            slots.append(current)
            current += step

        appointments = Appointment.objects.select_related("service").filter(
            doctor=doctor,
            preferred_datetime__date=day,
        )

        by_time = {
            timezone.localtime(a.preferred_datetime).replace(second=0, microsecond=0): a
            for a in appointments
        }

        rows = [{"dt": dt, "appointment": by_time.get(dt)} for dt in slots]

        context = dict(
            self.admin_site.each_context(request),
            title="Календарь врача",
            doctors=doctors,
            doctor=doctor,
            day=day,
            rows=rows,
            add_url=reverse("admin:appointments_appointment_add"),
        )

        return TemplateResponse(
            request,
            "admin/appointments/calendar.html",
            context,
        )
