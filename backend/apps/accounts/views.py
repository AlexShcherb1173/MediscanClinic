"""
Представления (views) приложения accounts.
Содержит:
- register_view — регистрация пользователя
- login_view — вход пользователя
- logout_view — выход из системы
"""

from __future__ import annotations

from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, RegisterForm

PHONE_BACKEND = "apps.accounts.backends.PhoneBackend"


@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Регистрирует нового пользователя (аутентификация по телефону)
    и автоматически выполняет вход.
    Если пользователь уже авторизован —
    выполняется редирект в личный кабинет.
    """
    if request.user.is_authenticated:
        return redirect("cabinet:dashboard")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend=PHONE_BACKEND)
        return redirect("cabinet:dashboard")

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Выполняет вход существующего пользователя по телефону.
    Если пользователь уже авторизован —
    выполняется редирект в личный кабинет.
    """
    if request.user.is_authenticated:
        return redirect("cabinet:dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        login(request, user, backend=PHONE_BACKEND)
        return redirect("cabinet:dashboard")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    """
    Выполняет выход пользователя из системы
    и перенаправляет на главную страницу.
    """
    logout(request)
    return redirect("pages:home")
