from django.urls import path
from orders.views.user.checkout import checkoutview, get_addresses


urlpatterns = [
    path("checkout/", checkoutview, name="checkout"),
    path("api/addresses/get/", get_addresses, name="get_addresses"),
]
