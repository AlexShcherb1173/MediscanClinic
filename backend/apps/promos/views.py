"""
Views for promos application.

Provides:
- promo_list: list of active promos
- promo_detail: promo details with active services
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404, render

from .models import Promo


def promo_list(request):
    """Render list of active promos ordered by sort_order then created_at desc."""
    promos = Promo.objects.filter(is_active=True).order_by("sort_order", "-created_at")
    return render(request, "promos/list.html", {"promos": promos})


def promo_detail(request, slug: str):
    """
    Render promo details page.

    Shows only active promo and related services which are active
    and have active categories.
    """
    promo = get_object_or_404(
        Promo.objects.prefetch_related("services", "services__category"),
        slug=slug,
        is_active=True,
    )

    promo_services = promo.services.filter(is_active=True, category__is_active=True)

    return render(
        request,
        "promos/detail.html",
        {"promo": promo, "promo_services": promo_services},
    )