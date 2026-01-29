from django.shortcuts import render, get_object_or_404
from .models import Page
from django.utils import timezone
from apps.promos.models import Promo


def page_detail(request, slug: str):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "pages/page_detail.html", {"page": page})

def home(request):
    promos = Promo.objects.filter(is_active=True).order_by("sort_order", "-created_at")[:3]
    return render(request, "pages/home.html", {"promos": promos})
