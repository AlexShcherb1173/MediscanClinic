from django.urls import path
from .views import doctor_list, doctor_detail

app_name = "staff"

urlpatterns = [
    path("", doctor_list, name="doctor_list"),
    path("<int:pk>/", doctor_detail, name="doctor_detail"),
]