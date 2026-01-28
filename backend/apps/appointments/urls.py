from django.urls import path
from .views import appointment_create, appointment_success, available_slots

app_name = "appointments"

urlpatterns = [
    path("create/", appointment_create, name="create"),
    path("success/<int:pk>/", appointment_success, name="success"),
    path("slots/", available_slots, name="slots"),
]