from django.urls import path
from .views import home, set_city

urlpatterns = [
    path("", home, name="home"),
    path("set-city/<int:city_id>/", set_city, name="set_city"),
]