from django.urls import path

from pages.views.user_pages import home, get_latest_product, get_mega_menu_data

urlpatterns = [
    path("", home, name="home"),
    path("api/latest-product/", get_latest_product, name="get_latest_product"),
    path("api/mega-menu/", get_mega_menu_data, name="get_mega_menu_data"),
]
