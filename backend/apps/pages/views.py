"""
Views for the pages application.

Responsibilities:
- Render home page (promos, popular services, doctors slider)
- Render static informational pages by slug (template-based)
- Render dynamic CMS-like pages stored in DB (Page model)
- Render sitemap page
"""

from django.shortcuts import get_object_or_404, render

from apps.promos.models import Promo
from apps.services.models import Service
from apps.staff.models import Doctor

from .models import Page

# Slugs that are rendered using dedicated templates (without DB Page records).
STATIC_TEMPLATES = {
    "about-history": "pages/about-history.html",
    "about-mission": "pages/about-mission.html",
    "about-quality": "pages/about-quality.html",
    "about-licenses": "pages/about-licenses.html",
    "privacy": "pages/privacy.html",
    "personal-data": "pages/personal-data.html",
}


def sitemap_view(request):
    """
    Render the sitemap page.

    This view is typically linked from the footer and may contain:
    - site section links
    - service categories
    - legal pages
    """
    return render(request, "pages/sitemap.html")


def page_detail(request, slug: str):
    """
    Render a page by slug.

    Routing rules:
    1) Special slug "about" renders a custom template with doctors and licenses.
    2) For certain slugs, render dedicated templates defined in STATIC_TEMPLATES.
    3) Otherwise, load a published Page from the database and render page_detail.

    Args:
        request: Django HttpRequest.
        slug: Page slug from URL.

    Returns:
        HttpResponse
    """
    # 1) Special "about" page with extra context
    if slug == "about":
        doctors = (
            Doctor.objects.filter(is_active=True)
            .prefetch_related("specialties")
            .order_by("full_name")[:6]
        )

        try:
            from apps.core.models import License

            licenses = License.objects.all()
        except Exception:
            licenses = []

        return render(
            request,
            "pages/about.html",
            {
                "doctors": doctors,
                "licenses": licenses,
            },
        )

    # 2) Template-based static pages
    tpl = STATIC_TEMPLATES.get(slug)
    if tpl:
        return render(request, tpl)

    # 3) Fallback: CMS-like Page from DB
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "pages/page_detail.html", {"page": page})


def home(request):
    """
    Render the homepage.

    Context includes:
    - active promos (limited)
    - featured services (limited)
    - random doctors slider items (photo required)

    Returns:
        HttpResponse
    """
    promos = Promo.objects.filter(is_active=True).order_by("sort_order", "-created_at")[
        :3
    ]

    popular_services = (
        Service.objects.filter(
            is_active=True,
            is_featured=True,
            category__is_active=True,
        )
        .select_related("category")
        .order_by("featured_order", "name")[:4]
    )

    doctors_slider = list(
        Doctor.objects.exclude(photo="")
        .exclude(photo__isnull=True)
        .only("full_name", "photo")
        .order_by("?")[:10]
    )

    return render(
        request,
        "pages/home.html",
        {
            "promos": promos,
            "popular_services": popular_services,
            "doctors_slider": doctors_slider,
        },
    )
