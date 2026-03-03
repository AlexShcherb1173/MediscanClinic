"""
Маршруты приложения accounts.
Определяет URL для:
- входа в систему (login)
- регистрации (register)
- выхода из системы (logout)
"""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
]
