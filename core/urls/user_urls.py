from django.urls import path

from core.views.user_pages import (
    home,
    get_latest_product,
    get_mega_menu_data,
    contact_us,
    shipping_service,
    returns_exchange,
    privacy_policy,
    terms_of_service,
    authenticity,
)

urlpatterns = [
    path("", home, name="home"),
    path("api/latest-product/", get_latest_product, name="get_latest_product"),
    path("api/mega-menu/", get_mega_menu_data, name="get_mega_menu_data"),
    # Static / informational pages
    path("contact/", contact_us, name="contact_us"),
    path("shipping/", shipping_service, name="shipping_service"),
    path("returns/", returns_exchange, name="returns_exchange"),
    path("privacy-policy/", privacy_policy, name="privacy_policy"),
    path("terms-of-service/", terms_of_service, name="terms_of_service"),
    path("authenticity/", authenticity, name="authenticity"),
]
