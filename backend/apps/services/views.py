"""
Представления приложения услуг (services).
Содержит:
- ServiceListView — каталог услуг с фильтрами (категория, поиск, диапазон цен) и сортировкой;
- ServiceDetailView — детальная страница услуги по slug.
Также включает вспомогательную функцию _to_decimal для безопасного парсинга
числовых параметров из query string.
"""

from decimal import Decimal, InvalidOperation

from django.views.generic import DetailView, ListView

from .models import Service, ServiceCategory


def _to_decimal(value: str | None) -> Decimal | None:
    """
    Безопасно преобразует строку в Decimal.
    Поддерживает десятичный разделитель как точку, так и запятую.
    Возвращает None, если значение пустое или не поддаётся парсингу.
    Параметры:
        value: Сырая строка (обычно из query-параметров).
    Возвращает:
        Decimal | None: Число Decimal или None при невалидном вводе.
    """
    if not value:
        return None

    try:
        return Decimal(value.replace(",", "."))
    except (InvalidOperation, AttributeError):
        return None


SORT_MAP = {
    "name": "name",
    "-name": "-name",
    "price": "price_from",
    "-price": "-price_from",
}
"""
Сопоставление допустимых ключей сортировки (query-параметр `sort`)
с выражениями ORM для order_by().
Поддерживаемые значения:
    - name, -name
    - price, -price  (сортировка по price_from)
"""


class ServiceListView(ListView):
    """
    Каталог услуг с фильтрацией, сортировкой и пагинацией.
    Фильтры:
        - category_slug (из URL): фильтрация по категории;
        - q: поиск по названию (icontains);
        - price_min / price_max: диапазон цен (применяется к price_from);
        - sort: сортировка по имени или цене.
    UX:
        Сохраняет текущий URL каталога (вместе с фильтрами и пагинацией)
        в сессии под ключом services_return_url, чтобы на детальной странице
        можно было сделать «Назад в каталог» без потери контекста.
    """

    model = Service
    template_name = "services/service_list.html"
    context_object_name = "services"
    paginate_by = 9

    def get(self, request, *args, **kwargs):
        """
        Сохраняет текущий URL каталога в сессию и рендерит страницу.
        Сохраняется полный путь (request.get_full_path()),
        включая query-параметры фильтров и номер страницы пагинации.
        """
        request.session["services_return_url"] = request.get_full_path()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Формирует queryset для каталога услуг.
        Базовые условия:
            - услуга активна (is_active=True);
            - категория активна (category__is_active=True).
        Затем применяются фильтры из URL и query-параметров:
            - category_slug;
            - q;
            - price_min / price_max;
            - sort.
        Возвращает:
            QuerySet[Service]: Отфильтрованный и отсортированный queryset.
        """
        qs = Service.objects.filter(is_active=True, category__is_active=True).select_related(
            "category"
        )

        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(name__icontains=q)

        price_min = _to_decimal(self.request.GET.get("price_min"))
        price_max = _to_decimal(self.request.GET.get("price_max"))

        if price_min is not None:
            qs = qs.filter(price_from__gte=price_min)
        if price_max is not None:
            qs = qs.filter(price_from__lte=price_max)

        sort = (self.request.GET.get("sort") or "name").strip()
        return qs.order_by(SORT_MAP.get(sort, "name"))

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст данные для UI фильтров и навигации.
        В контекст добавляются:
            - categories: активные категории услуг;
            - значения текущих фильтров (q, price_min, price_max, sort);
            - category_slug из URL (для подсветки активной категории).
        """
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = ServiceCategory.objects.filter(is_active=True)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["price_min"] = self.request.GET.get("price_min", "")
        ctx["price_max"] = self.request.GET.get("price_max", "")
        ctx["sort"] = self.request.GET.get("sort", "name")
        ctx["category_slug"] = self.kwargs.get("category_slug", "")
        return ctx


class ServiceDetailView(DetailView):
    """
    Детальная страница услуги.
    Загружает услугу по slug и ограничивает доступ только
    активными услугами из активных категорий.
    """

    model = Service
    template_name = "services/detail.html"
    context_object_name = "service"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """
        Ограничивает queryset детальной страницы.
        Возвращает только:
            - активные услуги;
            - услуги из активных категорий.
        Дополнительно использует select_related("category")
        для оптимизации запросов.
        """
        return Service.objects.select_related("category").filter(
            is_active=True,
            category__is_active=True,
        )

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст активные категории услуг.
        Категории используются для меню/сайдбара на детальной странице.
        """
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = ServiceCategory.objects.filter(is_active=True)
        return ctx
