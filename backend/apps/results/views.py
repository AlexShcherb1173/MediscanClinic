"""
Views for results application.

Provides:
- my_results: list patient's own results
- download_result: secure file download + mark as viewed
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
    Show current user's research results.

    Currently renders cabinet template to keep UX unified.
    """
    qs = ResearchResult.objects.filter(patient=request.user).order_by("-created_at")
    return render(request, "cabinet/results.html", {"results": qs})


@login_required
def download_result(request, pk: int):
    """
    Download a research result file.

    Security:
        - only owner can download (others get 404)
    Side effects:
        - marks result as viewed on first download
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
