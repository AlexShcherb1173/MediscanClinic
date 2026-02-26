"""
Context processors for core application.

Provides global template context:
- Site settings
- Active cities list
- Currently selected city (from session)

Used in base templates to avoid repeating logic in views.
"""

from .models import City, SiteSettings


def core_context(request):
    """
    Inject global data into template context.

    Adds:
        settings: first SiteSettings instance (singleton-like usage)
        cities: queryset of active cities
        current_city: city selected in session (if any)

    Args:
        request: Django HttpRequest object.

    Returns:
        dict: Context dictionary available in all templates.
    """
    settings = SiteSettings.objects.first()
    cities = City.objects.filter(is_active=True)

    current_city_id = request.session.get("city_id")
    current_city = City.objects.filter(id=current_city_id).first()

    return {
        "settings": settings,
        "cities": cities,
        "current_city": current_city,
    }