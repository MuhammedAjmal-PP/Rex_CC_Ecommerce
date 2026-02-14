from django.urls import path
from orders.views.user.place_order import place_order_view, order_success_view
from orders.views.user.checkout import checkoutview, get_addresses
from orders.views.user.user_orders import (
    order_invoice,
    order_list,
    order_detail,
    orderitem_detail,
)


urlpatterns = [
    path("checkout/", checkoutview, name="checkout"),
    path("api/addresses/get/", get_addresses, name="get_addresses"),
    path("place-order/", place_order_view, name="place_order"),
    path("order/<str:order_number>/success/", order_success_view, name="order_success"),
    path("orders/", order_list, name="user_order_list"),
    path("order/<str:order_number>/details/", order_detail, name="user_order_details"),
    path(
        "order/<str:order_number>/item/<int:item_id>/details/",
        orderitem_detail,
        name="user_order_item_details",
    ),
    path(
        "order/<str:order_number>/invoice/download", order_invoice, name="order_invoice"
    ),
]
