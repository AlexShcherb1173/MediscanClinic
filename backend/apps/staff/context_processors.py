from __future__ import annotations

from typing import Any

from django.conf import settings

from .models import Doctor


def doctor_slider_items(request) -> dict[str, Any]:
    """
    Глобальный контекст для шаблонов: список врачей с фото
    для hero-слайдера (используем media/doctors/...).
    """
    qs = (
        Doctor.objects
        .filter(is_active=True)
        .exclude(photo="")
        .only("id", "full_name", "photo")
        .order_by("?")[:12]  # случайные 12, чтобы было “живее”
    )

    items = []
    for d in qs:
        try:
            url = d.photo.url  # MEDIA_URL + путь
        except Exception:
            url = ""

        if not url:
            continue

        items.append(
            {
                "url": url,
                "name": d.full_name,
            }
        )

    return {"doctor_slider_items": items}