from django.urls import path
from .views import contacts_home

app_name = "contacts"

urlpatterns = [
    path("", contacts_home, name="home"),
]