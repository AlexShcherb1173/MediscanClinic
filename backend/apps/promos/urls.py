"""
URL configuration for promos application.
"""

from django.urls import path

from .views import promo_detail, promo_list

app_name = "promos"

urlpatterns = [
    path("", promo_list, name="list"),
    path("<slug:slug>/", promo_detail, name="detail"),
]
