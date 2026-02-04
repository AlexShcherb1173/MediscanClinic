from django.urls import path
from .views import promo_list, promo_detail

app_name = "promos"

urlpatterns = [
    path("", promo_list, name="list"),
    path("<slug:slug>/", promo_detail, name="detail"),
]