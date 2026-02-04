from django.urls import path
from .views import set_city, contacts

app_name = "core"

urlpatterns = [
    path("set-city/<int:city_id>/", set_city, name="set_city"),
    path("contacts/", contacts, name="contacts"),
]