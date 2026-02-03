from django.contrib import admin

from .models import Specialty, Doctor, DoctorSchedule


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "experience_years", "is_active")
    list_filter = ("is_active", "specialties")
    search_fields = ("full_name",)
    filter_horizontal = ("specialties",)
    ordering = ("full_name",)


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "weekday", "time_from", "time_to")
    list_filter = ("weekday", "doctor")
    search_fields = ("doctor__full_name",)
    ordering = ("doctor", "weekday", "time_from")