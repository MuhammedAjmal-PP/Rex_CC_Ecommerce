from django.urls import path
from coupons.views.admin.views import coupon_list, add_coupon, edit_coupon, delete_coupon

urlpatterns = [
    path("coupons/",                  coupon_list,   name="admin_coupons"),
    path("coupons/add/",              add_coupon,    name="admin_coupon_add"),
    path("coupons/<int:pk>/edit/",    edit_coupon,   name="admin_coupon_edit"),
    path("coupons/<int:pk>/delete/",  delete_coupon, name="admin_coupon_delete"),
]
