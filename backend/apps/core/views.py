"""
Core views for MediscanClinic project.

Contains:
- Homepage rendering
- Contacts page with feedback form processing
- City selection via session

These views operate with global site settings,
active cities and user session state.
"""

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import City, SiteSettings
from .forms import FeedbackForm
from .notifications import (
    FeedbackNotification,
    notify_feedback_email,
    notify_feedback_telegram,
)


def home(request):
    """
    Render the homepage.

    Context includes:
    - global site settings (singleton-like model)
    - active cities
    - currently selected city from session
    """
    settings = SiteSettings.objects.first()
    cities = City.objects.filter(is_active=True)

    current_city_id = request.session.get("city_id")
    current_city = City.objects.filter(id=current_city_id).first()

    return render(
        request,
        "pages/home.html",
        {
            "settings": settings,
            "cities": cities,
            "current_city": current_city,
        },
    )


def contacts(request):
    """
    Render contacts page and handle feedback form submission.

    GET:
        - Display empty feedback form.

    POST:
        - Validate form.
        - Create FeedbackNotification payload.
        - Send notifications via email and Telegram.
        - Show success/error messages.
        - Redirect after successful submission (PRG pattern).
    """
    settings = SiteSettings.objects.first()
    cities = City.objects.filter(is_active=True)

    current_city_id = request.session.get("city_id")
    current_city = City.objects.filter(id=current_city_id).first()

    if request.method == "POST":
        form = FeedbackForm(request.POST)

        if form.is_valid():
            payload = FeedbackNotification(
                name=form.cleaned_data["name"],
                contact=form.cleaned_data["contact"],
                message=form.cleaned_data["message"],
                page_url=request.build_absolute_uri(reverse("contacts")),
            )

            # Send notifications
            notify_feedback_email(payload)
            notify_feedback_telegram(payload)

            messages.success(
                request,
                "Спасибо! Сообщение отправлено. Мы свяжемся с вами в ближайшее время.",
            )

            # PRG pattern: prevent duplicate submissions
            return redirect("contacts")

        else:
            messages.error(
                request,
                "Проверьте форму: заполните все поля корректно.",
            )
    else:
        form = FeedbackForm()

    return render(
        request,
        "pages/_contacts_.html",
        {
            "settings": settings,
            "cities": cities,
            "current_city": current_city,
            "form": form,
        },
    )


def set_city(request, city_id: int):
    """
    Store selected city in session.

    Only active cities can be selected.
    After setting session value, redirects user
    back to referring page (fallback to root path).
    """
    city = get_object_or_404(City, id=city_id, is_active=True)

    request.session["city_id"] = city.id

    return redirect(request.META.get("HTTP_REFERER", "/"))