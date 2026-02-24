from django.urls import path
from .views import home, page_detail
from .views import sitemap_view

app_name = "pages"

urlpatterns = [
    path("", home, name="home"),
    path("page/<slug:slug>/", page_detail, name="page_detail"),
    path("sitemap/", sitemap_view, name="sitemap"),
]