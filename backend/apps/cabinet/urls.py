from django.urls import path
from . import views

app_name = "cabinet"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("appointments/", views.my_appointments, name="appointments"),
    path("results/", views.results, name="results"),
]