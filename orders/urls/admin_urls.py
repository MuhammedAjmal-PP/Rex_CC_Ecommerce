from django.urls import path

from orders.views.admin.orders import (
    order_detail,
    order_item_status_update,
    order_list,
    order_status_update,
)


urlpatterns = [
    path("orders/", order_list, name="admin_orders_list"),
    path(
        "orders/<str:order_number>/details/",
        order_detail,
        name="admin_order_detail",
    ),
    path(
        "orders/<str:order_number>/status/update/",
        order_status_update,
        name="admin_order_status_update",
    ),
    path(
        "orders/<str:order_number>/item/<int:item_id>/status/update/",
        order_item_status_update,
        name="admin_order_item_status_update",
    ),
]
