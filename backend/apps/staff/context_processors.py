"""
Контекстные процессоры приложения персонала (staff).
Добавляет глобальные данные в шаблоны для отображения
слайдера врачей на главной странице.
"""

from __future__ import annotations

from typing import Any

from .models import Doctor


def doctor_slider_items(request) -> dict[str, Any]:
    """
    Добавляет в контекст данные для hero-слайдера врачей.
    Логика:
        - выбираются только активные врачи (is_active=True);
        - врач должен иметь загруженную фотографию;
        - выполняется случайная выборка (order_by("?"));
        - ограничение — до 12 элементов;
        - формируется список словарей вида:
              {"url": <photo_url>, "name": <full_name>}.
    Параметры:
        request: HttpRequest текущего запроса (не используется напрямую,
                 но обязателен для сигнатуры context processor).
    Возвращает:
        dict: {"doctor_slider_items": list[dict[str, str]]}
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
