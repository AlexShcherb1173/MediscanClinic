from django.urls import path
from .views import ServiceListView, ServiceDetailView

app_name = "services"

urlpatterns = [
    path("", ServiceListView.as_view(), name="list"),
    path("category/<slug:category_slug>/", ServiceListView.as_view(), name="category"),
    path("<slug:slug>/", ServiceDetailView.as_view(), name="detail"),
]