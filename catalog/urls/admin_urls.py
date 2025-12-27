from django.urls import path
from catalog.views.admin.brand import (
    brands,
    brand_add,
    brand_edit,
    brand_status_toggle,
    brand_view,
)
from catalog.views.admin.category import (
    categories,
    category_add,
    category_edit,
    category_status_toggle,
)

from catalog.views.admin.product import (
    products,
    product_add,
    product_edit,
    product_view,
    product_delete_toggle,
    product_draft_toggle,
    variant_add,
    variant_edit,
    variant_view,
    variant_delete_toggle,
    variant_draft_toggle,
)

urlpatterns = [
    # brands
    path("brands/", brands, name="admin_brands"),
    path("brand/add/", brand_add, name="admin_brand_add"),
    path("brand/<int:id>/view", brand_view, name="admin_brand_view"),
    path("brand/<int:id>/edit/", brand_edit, name="admin_brand_edit"),
    path(
        "brand/<int:id>/stats-toggle/",
        brand_status_toggle,
        name="admin_brand_status_toggle",
    ),
    # categories
    path("categories/", categories, name="admin_categories"),
    path("category/add/", category_add, name="admin_category_add"),
    path("category/<int:id>/edit/", category_edit, name="admin_category_edit"),
    path(
        "category/<int:id>/stats-toggle/",
        category_status_toggle,
        name="admin_category_status_toggle",
    ),
    # products
    path("products/", products, name="admin_products"),
    path("product/add/", product_add, name="admin_product_add"),
    path("product/<int:id>/edit/", product_edit, name="admin_product_edit"),
    path(
        "product/<int:id>/delete-toggle/",
        product_delete_toggle,
        name="admin_product_delete_toggle",
    ),
    path(
        "product/<int:id>/draft-toggle/",
        product_draft_toggle,
        name="admin_product_draft_toggle",
    ),
    path("product/<int:id>/view/", product_view, name="admin_product_view"),
    # variants
    path(
        "product/<int:product_id>/variant/add/", variant_add, name="admin_variant_add"
    ),
    path(
        "product/<int:product_id>/variant/<int:variant_id>/edit/",
        variant_edit,
        name="admin_variant_edit",
    ),
    path(
        "product/<int:product_id>/variant/<int:variant_id>/view/",
        variant_view,
        name="admin_variant_view",
    ),
    path(
        "product/<int:product_id>/variant/<int:variant_id>/delete-toggle/",
        variant_delete_toggle,
        name="admin_variant_delete_toggle",
    ),
    path(
        "product/<int:product_id>/variant/<int:variant_id>/draft-toggle/",
        variant_draft_toggle,
        name="admin_variant_draft_toggle",
    ),
]
