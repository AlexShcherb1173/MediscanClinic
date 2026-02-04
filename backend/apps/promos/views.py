from django.shortcuts import get_object_or_404, render

from .models import Promo


def promo_list(request):
    promos = Promo.objects.filter(is_active=True).order_by("sort_order", "-created_at")
    return render(request, "promos/list.html", {"promos": promos})


def promo_detail(request, slug: str):
    promo = get_object_or_404(
        Promo.objects.prefetch_related("services", "services__category"),
        slug=slug,
        is_active=True,
    )

    # показываем только активные услуги (и активные категории)
    promo_services = promo.services.filter(is_active=True, category__is_active=True)

    return render(
        request,
        "promos/detail.html",
        {
            "promo": promo,
            "promo_services": promo_services,
        },
    )