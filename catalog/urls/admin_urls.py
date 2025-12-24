from django.urls import path
from catalog.views.admin.brand import (
    brand_list,
    brand_add,
    brand_edit,
    brand_status_toggle,
)


urlpatterns = [
    path("brands/", brand_list, name="admin_brands"),
    path("brand/add/", brand_add, name="admin_brand_add"),
    path("brand/<int:id>/edit/", brand_edit, name="admin_brand_edit"),
    path(
        "brand/<int:id>/stats-toggle/",
        brand_status_toggle,
        name="admin_brand_status_toggle",
    ),
]
