"""
URL configuration for core application.

Includes:
- City selection endpoint (stored in session)
- Contacts page with feedback form

All routes are namespaced under "core".
"""

from django.urls import path

from .views import set_city, contacts


app_name = "core"

urlpatterns = [
    # Store selected city in session
    path("set-city/<int:city_id>/", set_city, name="set_city"),

    # Contacts page and feedback form handling
    path("contacts/", contacts, name="contacts"),
]