from django.urls import path
from orders.views.user.place_order import place_order_view
from orders.views.user.razorpay import (
    razorpay_callback,
    razorpay_payment_failed,
    retry_razorpay_payment,
)
from orders.views.user.order_results import order_success_view, order_failure_view
from orders.views.user.checkout import checkoutview, get_addresses
from orders.views.user.user_orders import (
    order_invoice,
    order_list,
    order_detail,
)
from orders.views.user.cancel_order import (
    cancel_order,
    cancel_order_submit,
)
from orders.views.user.return_order import (
    return_order,
    return_order_submit,
)

urlpatterns = [
    path("checkout/", checkoutview, name="checkout"),
    path("api/addresses/get/", get_addresses, name="get_addresses"),
    path("place-order/", place_order_view, name="place_order"),
    path("razorpay/callback/", razorpay_callback, name="razorpay_callback"),
    path("razorpay/failed/", razorpay_payment_failed, name="razorpay_payment_failed"),
    path("razorpay/retry/", retry_razorpay_payment, name="retry_razorpay_payment"),
    path("order/<str:order_number>/success/", order_success_view, name="order_success"),
    path("order/<str:order_number>/failure/", order_failure_view, name="order_failure"),
    path("orders/", order_list, name="user_order_list"),
    path("order/<str:order_number>/details/", order_detail, name="user_order_details"),
    path(
        "order/<str:order_number>/invoice/download", order_invoice, name="order_invoice"
    ),
    path(
        "order/<str:order_number>/cancel/",
        cancel_order,
        name="user_cancel_order",
    ),
    path(
        "order/<str:order_number>/cancel/submit/",
        cancel_order_submit,
        name="user_cancel_order_submit",
    ),
    path(
        "order/<str:order_number>/item/<int:item_id>/return/",
        return_order,
        name="user_return_order",
    ),
    path(
        "order/<str:order_number>/item/<int:item_id>/return/submit/",
        return_order_submit,
        name="user_return_order_submit",
    ),
]
