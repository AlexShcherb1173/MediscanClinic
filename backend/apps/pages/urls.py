"""
Конфигурация URL для приложения страниц (pages).
Маршруты:
- home — главная страница сайта;
- page_detail — отображение статической страницы по slug;
- sitemap — страница карты сайта.
Используется пространство имён app_name = "pages"
для корректной работы reverse() и {% url %}.
"""

from django.urls import path

from .views import home, page_detail, sitemap_view

app_name = "pages"

urlpatterns = [
    path("", home, name="home"),
    path("page/<slug:slug>/", page_detail, name="page_detail"),
    path("sitemap/", sitemap_view, name="sitemap"),
]
