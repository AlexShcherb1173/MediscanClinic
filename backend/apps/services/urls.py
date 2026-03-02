"""
URL-маршруты приложения услуг (services).
Определяет:
- общий каталог услуг;
- каталог с фильтрацией по категории;
- страницу детального просмотра услуги.
"""

from django.urls import path

from .views import ServiceDetailView, ServiceListView

app_name = "services"

urlpatterns = [
    # Полный каталог услуг
    path("", ServiceListView.as_view(), name="list"),

    # Каталог услуг, отфильтрованный по slug категории
    path(
        "category/<slug:category_slug>/",
        ServiceListView.as_view(),
        name="category",
    ),

    # Детальная страница конкретной услуги
    path("<slug:slug>/", ServiceDetailView.as_view(), name="detail"),
]
