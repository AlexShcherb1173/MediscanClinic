"""
URL-маршруты приложения результатов исследований (results).
Определяет:
- страницу «Мои результаты» для пациента;
- скачивание конкретного результата по его идентификатору.
"""

from django.urls import path

from . import views

app_name = "results"

urlpatterns = [
    # Список результатов текущего пользователя
    path("", views.my_results, name="my_results"),

    # Скачивание PDF-файла результата по первичному ключу
    path("download/<int:pk>/", views.download_result, name="download"),
]
