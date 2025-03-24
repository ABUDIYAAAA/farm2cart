from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/get-prices", views.get_prices, name="get_prices"),
]
