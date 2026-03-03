"""
Конфигурация URL для приложения личного кабинета (cabinet).
Маршруты:
- dashboard — главная страница личного кабинета;
- appointments — список записей пользователя;
- results — список результатов исследований пользователя.
Используется пространство имён app_name = "cabinet"
для удобного reverse() и {% url %} в шаблонах.
"""

from django.urls import path

from . import views

app_name = "cabinet"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("appointments/", views.appointments_view, name="appointments"),
    path("results/", views.results_view, name="results"),
]
