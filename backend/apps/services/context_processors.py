"""
Context processors for services application.

Provides a queryset of featured services for homepage blocks and menus.
"""

from apps.services.models import Service


def popular_services(request):
    """
    Provide featured services for templates.

    Returns:
        dict: {"popular_services": queryset} where queryset contains up to 4
        active featured services from active categories.
    """
    qs = (
        Service.objects.filter(
            is_active=True,
            is_featured=True,
            category__is_active=True,
        )
        .select_related("category")
        .order_by("featured_order", "name")[:4]
    )
    return {"popular_services": qs}