from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "service", "preferred_datetime", "status", "created_at")
    list_filter = ("status", "service", "preferred_datetime")
    search_fields = ("full_name", "phone", "service__name")
    ordering = ("-created_at",)