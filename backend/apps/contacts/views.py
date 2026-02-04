from django.shortcuts import render
from apps.core.models import SiteSettings

def contacts_home(request):
    settings_obj = SiteSettings.objects.first()
    return render(request, "contacts/home.html", {"settings": settings_obj})