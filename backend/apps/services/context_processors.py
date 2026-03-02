"""
Контекстные процессоры приложения услуг (services).
Добавляет в шаблоны queryset популярных (featured) услуг
для отображения на главной странице и в навигационных блоках.
"""

from apps.services.models import Service


def popular_services(request):
    """
    Добавляет в контекст шаблонов популярные услуги.
    Логика:
        - выбираются только активные услуги (is_active=True);
        - услуга должна быть отмечена как избранная (is_featured=True);
        - категория услуги также должна быть активной;
        - сортировка по featured_order, затем по имени;
        - ограничение выборки — до 4 записей.
    Параметры:
        request: HttpRequest текущего запроса (не используется напрямую,
                 но обязателен для сигнатуры context processor).
    Возвращает:
        dict: {"popular_services": queryset}
    """
    qs = (
        Service.objects.filter(
            is_active=True,
            is_featured=True,
            category__is_active=True,
        )
        .select_related("category")
        .order_by("featured_order", "name")[:4]
    )
    return {"popular_services": qs}
