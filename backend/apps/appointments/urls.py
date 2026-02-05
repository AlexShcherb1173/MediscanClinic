from django.urls import path

from . import views
from .views import create, slot_options

app_name = "appointments"

urlpatterns = [
    path("create/", views.appointment_create, name="create"),
    path("slots/", slot_options, name="slots"),
    path("success/<int:pk>/", views.appointment_success, name="success"),
    path("calendar/", calendar_view, name="calendar"),
    path("slots/", views.appointment_slots, name="slots"),
]