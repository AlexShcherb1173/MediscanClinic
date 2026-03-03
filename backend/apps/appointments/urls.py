"""
Конфигурация URL для приложения записей на приём.
Маршруты:
- index — редирект/главная страница раздела записей;
- create — страница создания записи;
- slots — HTMX-эндпоинт для загрузки доступных слотов;
- calendar — HTMX-эндпоинт для отображения календаря;
- success — страница успешного создания записи.
Использует пространство имён app_name = "appointments"
для удобного reverse() и {% url %}.
"""

from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.appointments_index, name="index"),
    path("create/", views.appointment_create, name="create"),
    path("slots/", views.slots, name="slots"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("success/<int:pk>/", views.appointment_success, name="success"),
]
