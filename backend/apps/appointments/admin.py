"""
Админ-настройки для приложения appointments.
Возможности:
- список записей (Appointment) с кнопками «Подтвердить» / «Отменить»
- календарь врача в админке (дневной вид с шагом 20 минут)
- подсветка строк в списке в зависимости от статуса и времени приёма
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
    Интерфейс админки для модели Appointment.
    Дополнительно реализовано:
    - inline-кнопки для подтверждения/отмены записи прямо из списка
    - отдельная страница «Календарь врача» в админке
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
        """
        Регистрирует дополнительные URL-адреса админки:
        - /calendar/ — дневной календарь врача
        - /<pk>/confirm/ — подтвердить запись
        - /<pk>/cancel/ — отменить запись
        """
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
        """
        Рендерит кнопки «Подтвердить» / «Отменить» в колонке списка.
        """
        return format_html(
            "<a class='button' href='{}/confirm/'>✔ Confirm</a>&nbsp;"
            "<a class='button' style='color:#b91c1c' href='{}/cancel/'>✖ Cancel</a>",
            obj.pk,
            obj.pk,
        )

    action_buttons.short_description = "Действия"

    def confirm_appointment(self, request, pk):
        """
        Переводит запись в статус CONFIRMED (Подтверждена).
        """
        obj = Appointment.objects.get(pk=pk)
        obj.status = Appointment.Status.CONFIRMED
        obj.save(update_fields=["status"])
        messages.success(request, "Запись подтверждена")
        return redirect("..")

    def cancel_appointment(self, request, pk):
        """
        Переводит запись в статус CANCELED (Отменена).
        """
        obj = Appointment.objects.get(pk=pk)
        obj.status = Appointment.Status.CANCELED
        obj.save(update_fields=["status"])
        messages.warning(request, "Запись отменена")
        return redirect("..")

    def get_queryset(self, request):
        """
        Добавляет атрибут `row_class` для подсветки строк в шаблоне админки.
        Логика:
        - если запись подтверждена и время уже прошло — помечаем как «завершённую»
        - иначе класс формируется от статуса: status-<status>
        Примечание:
            Метод проходит по объектам queryset и присваивает атрибут в Python.
            Для очень больших списков это может быть тяжелее, но для админки обычно
            приемлемо.
        """
        qs = super().get_queryset(request)
        now = timezone.now()

        for obj in qs:
            if obj.preferred_datetime and obj.preferred_datetime < now and obj.status == Appointment.Status.CONFIRMED:
                obj.row_class = "status-completed"
            else:
                obj.row_class = f"status-{obj.status}"

        return qs

    def calendar_view(self, request):
        """
        Отображает дневной календарь врача с шагом 20 минут.
        GET-параметры:
            doctor: id врача
            date: дата в формате YYYY-MM-DD
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

        by_time = {timezone.localtime(a.preferred_datetime).replace(second=0, microsecond=0): a for a in appointments}

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
