"""
URL configuration for services application.

Routes:
- Service catalog (all services)
- Category-filtered catalog
- Service detail page
"""

from django.urls import path

from .views import ServiceDetailView, ServiceListView

app_name = "services"

urlpatterns = [
    # Full catalog
    path("", ServiceListView.as_view(), name="list"),
    # Catalog filtered by category
    path(
        "category/<slug:category_slug>/",
        ServiceListView.as_view(),
        name="category",
    ),
    # Service detail page
    path("<slug:slug>/", ServiceDetailView.as_view(), name="detail"),
]
