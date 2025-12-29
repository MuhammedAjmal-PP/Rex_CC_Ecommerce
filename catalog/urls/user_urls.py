from django.urls import path

from catalog.views.user.product import product_list

urlpatterns = [
    path("products/", product_list, name="product_list"),
]
