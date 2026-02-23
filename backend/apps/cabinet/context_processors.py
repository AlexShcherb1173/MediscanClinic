from apps.results.models import ResearchResult


def cabinet_badges(request):
    if not request.user.is_authenticated:
        return {"unread_results_count": 0}

    cnt = ResearchResult.objects.filter(
        patient=request.user,
        is_viewed=False,
    ).count()

    return {"unread_results_count": cnt}