"""
Views for accounts application.

Provides:
- register_view
- login_view
- logout_view
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
    Register new user (phone-based) and log them in.
    Redirects authenticated users to dashboard.
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
    Log in existing user.
    Redirects authenticated users to dashboard.
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
    """Log out and redirect to homepage."""
    logout(request)
    return redirect("pages:home")
