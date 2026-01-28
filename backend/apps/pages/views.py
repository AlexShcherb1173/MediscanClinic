from django.shortcuts import render, get_object_or_404
from .models import Page


def page_detail(request, slug: str):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "pages/page_detail.html", {"page": page})
