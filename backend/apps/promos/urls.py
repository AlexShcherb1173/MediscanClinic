"""
URL-маршруты приложения акций (promos).
Определяет:
- список акций;
- детальную страницу акции по slug.
"""

from django.urls import path

from .views import promo_detail, promo_list

app_name = "promos"

urlpatterns = [
    # Список всех активных акций
    path("", promo_list, name="list"),
    # Детальная страница акции по slug
    path("<slug:slug>/", promo_detail, name="detail"),
]
