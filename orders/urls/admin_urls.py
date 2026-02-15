from django.urls import path
from orders.views.admin.orders import order_list


urlpatterns = [
    path("orders/", order_list, name="admin_orders_list"),
]
