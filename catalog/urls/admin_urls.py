from django.urls import path
from catalog.views.admin.brand import brand_list, brand_add


urlpatterns = [
    path("brands/", brand_list, name="admin_brands"),
    path("brand/add/", brand_add, name="admin_brand_add"),
]
