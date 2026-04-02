from django.urls import path
from coupons.views.user.views import apply_coupon, remove_coupon

urlpatterns = [
    path("coupon/apply/", apply_coupon, name="apply_coupon"),
    path("coupon/remove/", remove_coupon, name="remove_coupon"),
]
