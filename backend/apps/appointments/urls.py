from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("create/", views.appointment_create, name="create"),
    path("success/<int:pk>/", views.appointment_success, name="success"),
    path("slots/", views.appointment_slots, name="slots"),
]