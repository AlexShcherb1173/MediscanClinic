from django.shortcuts import get_object_or_404
from decimal import Decimal, InvalidOperation
from django.views.generic import ListView, DetailView

from .models import Service, ServiceCategory


def _to_decimal(v: str | None) -> Decimal | None:
    if not v:
        return None
    try:
        return Decimal(v.replace(",", "."))
    except (InvalidOperation, AttributeError):
        return None


SORT_MAP = {
    "name": "name",
    "-name": "-name",
    "price": "price_from",
    "-price": "-price_from",
}


class ServiceListView(ListView):
    model = Service
    template_name = "services/list.html"
    context_object_name = "services"
    paginate_by = 9

    def get_queryset(self):
        qs = Service.objects.filter(is_active=True, category__is_active=True).select_related("category")

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
        qs = qs.order_by(SORT_MAP.get(sort, "name"))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = ServiceCategory.objects.filter(is_active=True)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["price_min"] = self.request.GET.get("price_min", "")
        ctx["price_max"] = self.request.GET.get("price_max", "")
        ctx["sort"] = self.request.GET.get("sort", "name")
        ctx["category_slug"] = self.kwargs.get("category_slug", "")
        return ctx

class ServiceDetailView(DetailView):
    model = Service
    template_name = "services/detail.html"
    context_object_name = "service"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Service.objects.select_related("category")
            .filter(is_active=True, category__is_active=True)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = ServiceCategory.objects.filter(is_active=True)  # если хочешь меню слева и на деталке
        return ctx