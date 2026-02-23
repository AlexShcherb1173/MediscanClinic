from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import ResearchResult


@login_required
def my_results(request):
    qs = ResearchResult.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "results/my_results.html", {"results": qs})

@login_required
def download_result(request, pk: int):
    result = get_object_or_404(ResearchResult, pk=pk)

    # 🔒 запрет чужих файлов
    if result.patient_id != request.user.id:
        raise Http404("Not found")

    # ⭐ помечаем как просмотренное при скачивании
    if not result.is_viewed:
        result.is_viewed = True
        result.viewed_at = timezone.now()
        result.save(update_fields=["is_viewed", "viewed_at"])

    # Защищённая отдача файла
    # as_attachment=True -> скачивание, filename -> нормальное имя
    return FileResponse(
        result.file.open("rb"),
        as_attachment=True,
        filename=result.file.name.split("/")[-1],
        content_type="application/pdf",
    )
