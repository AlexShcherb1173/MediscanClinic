"""
Представления приложения акций (promos).
Реализует:
- список активных акций;
- детальную страницу акции с отображением связанных услуг.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404, render

from .models import Promo


def promo_list(request):
    """
    Отображает список активных акций.
    В выборку попадают только объекты Promo с is_active=True.
    Сортировка:
        - по полю sort_order (по возрастанию);
        - затем по created_at (по убыванию).
    Параметры:
        request: HttpRequest текущего запроса.
    Возвращает:
        HttpResponse со списком акций.
    """
    promos = Promo.objects.filter(is_active=True).order_by("sort_order", "-created_at")
    return render(request, "promos/list.html", {"promos": promos})


def promo_detail(request, slug: str):
    """
    Отображает детальную страницу акции.
    Логика:
        - загружается только активная акция по slug;
        - дополнительно подгружаются связанные услуги и их категории;
        - отображаются только услуги:
            * is_active=True;
            * категория услуги также активна.
    Параметры:
        request: HttpRequest текущего запроса.
        slug: строковый идентификатор акции из URL.
    Возвращает:
        HttpResponse со страницей акции.
    """
    promo = get_object_or_404(
        Promo.objects.prefetch_related("services", "services__category"),
        slug=slug,
        is_active=True,
    )
    # Фильтруем только актуальные услуги акции:
    # - услуга активна (is_active=True)
    # - категория услуги также активна
    promo_services = promo.services.filter(is_active=True, category__is_active=True)
    """
    Формируем queryset услуг, участвующих в акции.
    Условия:
        - услуга должна быть активной;
        - категория услуги также должна быть активной.
    """

    return render(
        request,
        "promos/detail.html",
        {"promo": promo, "promo_services": promo_services},
    )
