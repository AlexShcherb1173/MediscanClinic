"""
URL configuration for staff application.

Routes:
- list of doctors
- doctor detail page by pk
"""

from django.urls import path

from .views import doctor_detail, doctor_list


app_name = "staff"

urlpatterns = [
    path("", doctor_list, name="doctor_list"),
    path("<int:pk>/", doctor_detail, name="doctor_detail"),
]