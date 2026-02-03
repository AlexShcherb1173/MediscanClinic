from django.shortcuts import render, get_object_or_404
from .models import Page
from apps.promos.models import Promo
from apps.services.models import Service


def page_detail(request, slug: str):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "pages/page_detail.html", {"page": page})


def home(request):
    promos = Promo.objects.filter(is_active=True).order_by("sort_order", "-created_at")[:3]

    popular_services = (
        Service.objects
        .filter(is_active=True, is_featured=True, category__is_active=True)
        .select_related("category")
        .order_by("featured_order", "name")[:4]
    )

    return render(
        request,
        "pages/home.html",
        {
            "promos": promos,
            "popular_services": popular_services,
        },
    )
