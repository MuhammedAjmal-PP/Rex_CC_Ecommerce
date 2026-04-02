from django.urls import path

from users.cart.views import (
    add_cart,
    get_variant_stock,
    update_cart_quantity,
    remove_cart_item,
    view_cart,
    get_cartitems_count,
)

urlpatterns = [
    path("mycart/", view_cart, name="user_cart"),
    path(
        "api/<slug:slug>/v/<str:sku>/stock/fetch/",
        get_variant_stock,
        name="api_stock_fetch",
    ),
    path(
        "api/mycart/<slug:slug>/v/<str:sku>/add/",
        add_cart,
        name="add_cart",
    ),
    path(
        "api/mycart/<slug:slug>/v/<str:sku>/update/",
        update_cart_quantity,
        name="update_cart_quantity",
    ),
    path(
        "api/mycart/<slug:slug>/v/<str:sku>/remove/",
        remove_cart_item,
        name="remove_cart_item",
    ),
    path("api/mycart/count/", get_cartitems_count, name="get_cartitems_count"),
]
