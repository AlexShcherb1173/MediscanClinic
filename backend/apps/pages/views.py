from django.shortcuts import render, get_object_or_404

from .models import Page
from apps.promos.models import Promo
from apps.services.models import Service
from apps.core.models import City, SiteSettings
from apps.staff.models import Doctor
from apps.core.models import License
from django.shortcuts import render


# Слаги, которые рендерим шаблонами (без Page из БД)
STATIC_TEMPLATES = {
    "about-history": "pages/about-history.html",
    "about-mission": "pages/about-mission.html",
    "about-quality": "pages/about-quality.html",
    "about-licenses": "pages/about-licenses.html",
    "privacy": "pages/privacy.html",
    "personal-data": "pages/personal-data.html",
}


def sitemap_view(request):
    return render(request, "pages/sitemap.html")

def page_detail(request, slug: str):
    # 1) Спец-страница "about" (как у тебя) — с докторами и лицензиями
    if slug == "about":
        doctors = (
            Doctor.objects
            .filter(is_active=True)
            .prefetch_related("specialties")
            .order_by("full_name")[:6]
        )

        licenses = []
        if License is not None:
            licenses = (
                License.objects
                .filter(is_active=True)
                .order_by("sort_order", "-created_at")[:12]
            )

        return render(request, "pages/about.html", {
            "doctors": doctors,
            "licenses": licenses,
        })

    # 2) Страницы “шаблонные” (about-history / privacy / etc.)
    tpl = STATIC_TEMPLATES.get(slug)
    if tpl:
        return render(request, tpl, {})

    # 3) Fallback: обычные страницы из БД (Page)
    page = get_object_or_404(Page, slug=slug, is_published=True)

    # Если у тебя есть общий шаблон под Page, например pages/page_detail.html:
    return render(request, "pages/page_detail.html", {"page": page})

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
        {"promos": promos, "popular_services": popular_services},
    )