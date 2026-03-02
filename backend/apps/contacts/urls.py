"""
Конфигурация URL для приложения контактов (contacts).
Маршруты:
- home — основная страница «Контакты»;
- feedback — страница обратной связи;
- ask_question — форма отправки вопроса.
Используется пространство имён app_name = "contacts"
для корректной работы reverse() и {% url %} в шаблонах.
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
