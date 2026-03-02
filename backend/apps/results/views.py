"""
Представления приложения результатов исследований (results).
Реализует:
- отображение списка результатов текущего пользователя;
- безопасное скачивание PDF-файла результата;
- отметку результата как просмотренного.
"""

from __future__ import annotations

import os

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import ResearchResult

@login_required
def my_results(request):
    """
    Отображает список результатов исследований текущего пользователя.
    Логика:
        - выбираются только результаты, принадлежащие request.user;
        - сортировка по дате загрузки (новые сверху);
        - используется шаблон кабинета для единого UX.
    Доступ:
        Требуется аутентификация пользователя.
    """
    qs = ResearchResult.objects.filter(patient=request.user).order_by("-created_at")
    return render(request, "cabinet/results.html", {"results": qs})

@login_required
def download_result(request, pk: int):
    """
    Скачивание PDF-файла результата исследования.
    Безопасность:
        - файл может скачать только владелец результата;
        - при отсутствии файла возвращается 404.
    Побочные эффекты:
        - при первом скачивании результат помечается как просмотренный
          (is_viewed=True, viewed_at=текущее время).
    Параметры:
        request: HttpRequest текущего запроса.
        pk: первичный ключ объекта ResearchResult.
    Возвращает:
        FileResponse с вложением (application/pdf).
    """
    result = get_object_or_404(ResearchResult, pk=pk, patient=request.user)

    if not result.file:
        raise Http404("File not found")

    if not result.is_viewed:
        result.is_viewed = True
        result.viewed_at = timezone.now()
        result.save(update_fields=["is_viewed", "viewed_at"])

    filename = os.path.basename(result.file.name)

    return FileResponse(
        result.file.open("rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )
