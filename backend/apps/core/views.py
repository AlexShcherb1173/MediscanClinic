from django.shortcuts import render, redirect, get_object_or_404
from .models import City, SiteSettings


def home(request):
    settings = SiteSettings.objects.first()
    cities = City.objects.filter(is_active=True)
    current_city_id = request.session.get("city_id")
    current_city = City.objects.filter(id=current_city_id).first()
    return render(
        request,
        "core/home.html",
        {"settings": settings, "cities": cities, "current_city": current_city},
    )


def set_city(request, city_id: int):
    city = get_object_or_404(City, id=city_id, is_active=True)
    request.session["city_id"] = city.id
    return redirect(request.META.get("HTTP_REFERER", "/"))
