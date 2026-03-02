"""
Контекстные процессоры приложения личного кабинета (cabinet).
Добавляет в шаблоны данные для отображения бейджей в шапке,
в частности — счётчик непросмотренных результатов исследований.
"""

from __future__ import annotations

from apps.results.models import ResearchResult


def cabinet_badges(request) -> dict[str, int]:
    """
    Добавляет в контекст шаблонов количество непросмотренных результатов.
    Логика:
        - если пользователь не аутентифицирован — возвращается 0;
        - если пользователь авторизован — считается количество объектов
          ResearchResult с patient=request.user и is_viewed=False.
    Параметры:
        request (HttpRequest): Текущий HTTP-запрос.
    Возвращает:
        dict[str, int]: Словарь вида {"unread_results_count": int}.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"unread_results_count": 0}

    cnt = ResearchResult.objects.filter(patient=request.user, is_viewed=False).count()
    return {"unread_results_count": cnt}
