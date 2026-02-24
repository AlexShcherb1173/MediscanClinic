import os

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import ResearchResult


@login_required
def my_results(request):
    # ✅ у модели поле patient, не user
    qs = ResearchResult.objects.filter(patient=request.user).order_by("-created_at")

    # если хочешь отдельную страницу результатов вне ЛК — оставляй results/my_results.html
    # но если всё в ЛК — лучше рендерить cabinet/results.html
    return render(request, "cabinet/results.html", {"results": qs})


@login_required
def download_result(request, pk: int):
    result = get_object_or_404(ResearchResult, pk=pk)

    # 🔒 запрет чужих файлов
    if result.patient_id != request.user.id:
        raise Http404("Not found")

    # ✅ если файла нет — 404
    if not result.file:
        raise Http404("File not found")

    # ⭐ помечаем как просмотренное при скачивании
    if not result.is_viewed:
        result.is_viewed = True
        result.viewed_at = timezone.now()
        result.save(update_fields=["is_viewed", "viewed_at"])

    # нормальное имя файла (uuid.pdf)
    filename = os.path.basename(result.file.name)

    return FileResponse(
        result.file.open("rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )