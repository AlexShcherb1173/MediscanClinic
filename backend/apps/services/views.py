"""
Views for services application.

Includes:
- ServiceListView: catalog with filters (category, search, price range) and sorting
- ServiceDetailView: service detail page by slug

Also includes helper `_to_decimal` for safe parsing of numeric query parameters.
"""

from decimal import Decimal, InvalidOperation

from django.views.generic import DetailView, ListView

from .models import Service, ServiceCategory


def _to_decimal(value: str | None) -> Decimal | None:
    """
    Convert a string to Decimal safely.

    Accepts both dot and comma as decimal separators.
    Returns None if input is empty or cannot be parsed.

    Args:
        value: Raw string value (e.g. from query params).

    Returns:
        Decimal or None.
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
Mapping of supported sort keys (query param `sort`) to ORM order_by expressions.

Supported values:
- name, -name
- price, -price   (sort by price_from)
"""


class ServiceListView(ListView):
    """
    Service catalog page with filtering, sorting and pagination.

    Filters:
    - category (by category_slug in URL)
    - search by name (q)
    - price range (price_min/price_max applied to price_from)
    - sorting by name or price_from

    Additionally stores current catalog URL in session as `services_return_url`
    to support "Back to catalog" UX on detail page.
    """

    model = Service
    template_name = "services/service_list.html"
    context_object_name = "services"
    paginate_by = 9

    def get(self, request, *args, **kwargs):
        """
        Persist current catalog URL in session and render page.

        This stores full path including filters and pagination.
        """
        request.session["services_return_url"] = request.get_full_path()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Build queryset for the service catalog.

        Returns only active services from active categories,
        applies filters from URL and query parameters.
        """
        qs = (
            Service.objects.filter(is_active=True, category__is_active=True)
            .select_related("category")
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
        Add UI context for filters and navigation.
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
    Service details page.

    Fetches a service by slug and restricts queryset to active services
    from active categories.
    """

    model = Service
    template_name = "services/detail.html"
    context_object_name = "service"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """
        Restrict queryset to active services and active categories.
        """
        return Service.objects.select_related("category").filter(
            is_active=True,
            category__is_active=True,
        )

    def get_context_data(self, **kwargs):
        """
        Add active categories for menu/sidebar on detail page.
        """
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = ServiceCategory.objects.filter(is_active=True)
        return ctx