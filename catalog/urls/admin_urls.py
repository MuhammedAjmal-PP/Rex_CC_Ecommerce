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
    # Categories
    path("categories/", categories, name="admin_categories"),
]
