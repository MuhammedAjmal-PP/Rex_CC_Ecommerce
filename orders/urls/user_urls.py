from django.urls import path
from orders.views.user.place_order import place_order_view, order_success_view
from orders.views.user.checkout import checkoutview, get_addresses
from orders.views.user.user_orders import order_list


urlpatterns = [
    path("checkout/", checkoutview, name="checkout"),
    path("api/addresses/get/", get_addresses, name="get_addresses"),
    path("place-order/", place_order_view, name="place_order"),
    path("order/<str:order_number>/success/", order_success_view, name="order_success"),
    path("orders/", order_list, name="order_list"),
]
