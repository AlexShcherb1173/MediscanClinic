from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import ResearchResult


@login_required
def my_results(request):
    qs = ResearchResult.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "results/my_results.html", {"results": qs})
