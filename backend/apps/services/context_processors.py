from apps.services.models import Service


def popular_services(request):
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