from django.urls import path
from . import views

app_name = "appointments"

urlpatterns = [
    path("create/", views.appointment_create, name="create"),
    path("slots/", views.slots, name="slots"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("success/<int:pk>/", views.appointment_success, name="success"),
]
