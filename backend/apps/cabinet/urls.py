"""
URL configuration for cabinet application.
"""

from django.urls import path

from . import views

app_name = "cabinet"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("appointments/", views.appointments_view, name="appointments"),
    path("results/", views.results_view, name="results"),
]
