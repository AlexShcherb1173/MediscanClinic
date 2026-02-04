from .models import City, SiteSettings

def core_context(request):
    settings = SiteSettings.objects.first()
    cities = City.objects.filter(is_active=True)

    current_city_id = request.session.get("city_id")
    current_city = City.objects.filter(id=current_city_id).first()

    return {
        "settings": settings,
        "cities": cities,
        "current_city": current_city,
    }