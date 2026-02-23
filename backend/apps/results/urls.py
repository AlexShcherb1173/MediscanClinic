from django.urls import path
from . import views

app_name = "results"

urlpatterns = [
    path("", views.my_results, name="my_results"),
]