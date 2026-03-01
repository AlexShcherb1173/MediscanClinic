"""
Context processors for staff application.

Provides global template context for the homepage hero slider:
- doctor_slider_items: list of doctors with photos (url + name)
"""

from __future__ import annotations

from typing import Any

from .models import Doctor


def doctor_slider_items(request) -> dict[str, Any]:
    """
    Add doctors with photos for hero slider.

    Returns:
        dict with key "doctor_slider_items" -> list[{"url": str, "name": str}]
    """
    qs = (
        Doctor.objects.filter(is_active=True)
        .exclude(photo="")
        .only("id", "full_name", "photo")
        .order_by("?")[:12]
    )

    items: list[dict[str, str]] = []
    for d in qs:
        try:
            url = d.photo.url
        except Exception:
            url = ""

        if url:
            items.append({"url": url, "name": d.full_name})

    return {"doctor_slider_items": items}
