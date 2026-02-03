from datetime import datetime, time, timedelta

from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import Appointment
from apps.staff.models import Doctor


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
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

    # ==========================
    # КНОПКИ Confirm / Cancel
    # ==========================
    def get_urls(self):
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
        return (
            f'<a class="button" href="{obj.pk}/confirm/">✔ Confirm</a>&nbsp;'
            f'<a class="button" style="color:#b91c1c" href="{obj.pk}/cancel/">✖ Cancel</a>'
        )

    action_buttons.short_description = "Действия"
    action_buttons.allow_tags = True

    def confirm_appointment(self, request, pk):
        obj = Appointment.objects.get(pk=pk)
        obj.status = Appointment.Status.CONFIRMED
        obj.save(update_fields=["status"])
        messages.success(request, "Запись подтверждена")
        return redirect("..")

    def cancel_appointment(self, request, pk):
        obj = Appointment.objects.get(pk=pk)
        obj.status = Appointment.Status.CANCELED
        obj.save(update_fields=["status"])
        messages.warning(request, "Запись отменена")
        return redirect("..")

    # ==========================
    # ПОДСВЕТКА СТРОК
    # ==========================
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        now = timezone.now()

        for obj in qs:
            if obj.preferred_datetime < now and obj.status == Appointment.Status.CONFIRMED:
                obj.row_class = "status-completed"
            else:
                obj.row_class = f"status-{obj.status}"

        return qs

    # ==========================
    # КАЛЕНДАРЬ ВРАЧА
    # ==========================
    def calendar_view(self, request):
        doctor_id = request.GET.get("doctor")
        date_str = request.GET.get("date")

        day = parse_date(date_str) if date_str else timezone.localdate()
        if not day:
            day = timezone.localdate()

        doctors = Doctor.objects.filter(is_active=True).order_by("full_name")
        doctor = doctors.filter(pk=doctor_id).first() if doctor_id else doctors.first()

        # --- генерируем слоты (20 минут, 08:00–20:40)
        start_time = time(8, 0)
        end_time = time(20, 40)
        step = timedelta(minutes=20)

        slots = []
        current = datetime.combine(day, start_time)
        end_dt = datetime.combine(day, end_time)

        while current <= end_dt:
            slots.append(current)
            current += step

        # --- записи врача на день
        appointments = Appointment.objects.select_related("service").filter(
            doctor=doctor,
            preferred_datetime__date=day,
        )

        by_time = {
            timezone.localtime(a.preferred_datetime).replace(second=0, microsecond=0): a
            for a in appointments
        }

        # --- СОБИРАЕМ rows (ВАЖНО!)
        rows = []
        for dt in slots:
            rows.append({
                "dt": dt,
                "appointment": by_time.get(dt),
            })

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
