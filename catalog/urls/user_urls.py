from django.urls import path

from catalog.views.user.product import product_list, product_detail

urlpatterns = [
    path("products/", product_list, name="product_list"),
    path("product/<slug:slug>/", product_detail, name="product_detail"),
]
