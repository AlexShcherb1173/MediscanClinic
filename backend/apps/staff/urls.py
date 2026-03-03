"""
URL-маршруты приложения персонала (staff).
Определяет:
- страницу со списком врачей;
- страницу детального просмотра врача по его идентификатору (pk).
"""

from django.urls import path

from .views import doctor_detail, doctor_list

app_name = "staff"

urlpatterns = [
    # Список всех активных врачей
    path("", doctor_list, name="doctor_list"),
    # Детальная страница врача по первичному ключу
    path("<int:pk>/", doctor_detail, name="doctor_detail"),
]
