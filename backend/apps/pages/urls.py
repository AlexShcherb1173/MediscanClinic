"""
URL configuration for pages application.

Routes:
- Home page
- Dynamic/static page by slug
- Sitemap page
"""

from django.urls import path

from .views import home, page_detail, sitemap_view

app_name = "pages"

urlpatterns = [
    path("", home, name="home"),
    path("page/<slug:slug>/", page_detail, name="page_detail"),
    path("sitemap/", sitemap_view, name="sitemap"),
]
