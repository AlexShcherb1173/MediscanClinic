"""
URL configuration for contacts application.
"""

from django.urls import path

from . import views
from .views import contacts_home

app_name = "contacts"

urlpatterns = [
    path("", contacts_home, name="home"),
    path("feedback/", views.feedback_home, name="feedback"),
    path("ask-question/", views.ask_question, name="ask_question"),
]
