"""
Context processors for cabinet application.

Provides unread results counter for header badges.
"""

from __future__ import annotations

from apps.results.models import ResearchResult


def cabinet_badges(request) -> dict[str, int]:
    """
    Add unread results count to template context.

    Returns:
        {"unread_results_count": int}
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"unread_results_count": 0}

    cnt = ResearchResult.objects.filter(patient=request.user, is_viewed=False).count()
    return {"unread_results_count": cnt}
