"""
Представления приложения страниц (pages).
Ответственность:
- отображение главной страницы (акции, популярные услуги, слайдер врачей);
- отображение статических информационных страниц по slug (шаблонные страницы);
- отображение динамических CMS-страниц из базы данных (модель Page);
- отображение страницы карты сайта.
"""

from django.shortcuts import get_object_or_404, render

from apps.promos.models import Promo
from apps.services.models import Service
from apps.staff.models import Doctor

from .models import Page

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
    Отображает страницу карты сайта.
    Обычно содержит:
        - ссылки на основные разделы сайта;
        - категории и услуги;
        - юридические и информационные страницы.
    Возвращает:
        HttpResponse с шаблоном pages/sitemap.html.
    """
    return render(request, "pages/sitemap.html")


def page_detail(request, slug: str):
    """
    Отображает страницу по slug.
    Правила маршрутизации:
        1) Специальный slug "about" — рендерит отдельный шаблон
           с дополнительным контекстом (врачи и лицензии).
        2) Если slug присутствует в STATIC_TEMPLATES —
           используется соответствующий статический шаблон.
        3) В остальных случаях загружается опубликованная страница Page
           из базы данных (is_published=True).
    Параметры:
        request: Django HttpRequest.
        slug (str): Идентификатор страницы из URL.
    Возвращает:
        HttpResponse с соответствующим шаблоном.
    Исключения:
        Http404 — если страница не найдена или не опубликована.
    """
    if slug == "about":
        doctors = Doctor.objects.filter(is_active=True).prefetch_related("specialties").order_by("full_name")[:6]

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

    tpl = STATIC_TEMPLATES.get(slug)
    if tpl:
        return render(request, tpl)

    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "pages/page_detail.html", {"page": page})


def home(request):
    """
    Отображает главную страницу сайта.
    Формирует контекст:
        - активные акции (ограниченное количество);
        - популярные услуги (is_featured=True);
        - случайные врачи для слайдера (только с фото).
    Оптимизация:
        - используется select_related для категорий услуг;
        - ограничивается выборка (slice);
        - в слайдер загружаются только необходимые поля (only).
    Возвращает:
        HttpResponse с шаблоном pages/home.html.
    """
    promos = Promo.objects.filter(is_active=True).order_by("sort_order", "-created_at")[:3]

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
        Doctor.objects.exclude(photo="").exclude(photo__isnull=True).only("full_name", "photo").order_by("?")[:10]
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
