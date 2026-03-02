"""
Конфигурация административного интерфейса приложения персонала (staff).
Регистрирует модели:
- Specialty — медицинские специализации;
- Doctor — врачи;
- DoctorSchedule — расписание работы врачей.
Обеспечивает удобное управление персоналом через админ-панель.
"""

from django.contrib import admin

from .models import Doctor, DoctorSchedule, Specialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Specialty (специализация).
    Возможности:
        - отображение списка специализаций;
        - поиск по названию;
        - сортировка по алфавиту.
    """

    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Doctor (врач).
    Возможности:
        - отображение основного списка врачей;
        - фильтрация по активности и специализациям;
        - поиск по ФИО;
        - удобное редактирование связей many-to-many (specialties);
        - сортировка по ФИО.
    """

    list_display = ("id", "full_name", "experience_years", "is_active")
    list_filter = ("is_active", "specialties")
    search_fields = ("full_name",)
    filter_horizontal = ("specialties",)
    ordering = ("full_name",)


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели DoctorSchedule (расписание врача).
    Возможности:
        - отображение расписания по врачу и дню недели;
        - фильтрация по врачу и дню недели;
        - поиск по ФИО врача;
        - сортировка по врачу, дню недели и времени начала.
    """

    list_display = ("id", "doctor", "weekday", "time_from", "time_to")
    list_filter = ("weekday", "doctor")
    search_fields = ("doctor__full_name",)
    ordering = ("doctor", "weekday", "time_from")
