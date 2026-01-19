from django.urls import path

from pages.views.user_pages import home, get_latest_product

urlpatterns = [
    path("", home, name="home"),
    path("api/latest-product/", get_latest_product, name="get_latest_product"),
]
