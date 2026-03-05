"""
Order result pages — success and failure.
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from orders.models import Order
from orders.utils import get_payment_transaction


@login_required
@never_cache
def order_success_view(request, order_number):
    """Order success page — shows order summary after successful placement."""

    order = get_object_or_404(
        Order.objects.prefetch_related("payment"),
        user=request.user,
        order_number=order_number,
    )

    current_status = order.status

    # Sanity check: redirect away if order isn't in expected post-placement state
    payment = get_payment_transaction(order)
    if payment:
        if payment.payment_method == "COD" and current_status != "PLACED":
            return redirect("user_order_list")
        elif payment.payment_method != "COD" and current_status != "CONFIRMED":
            return redirect("user_order_list")

    return render(request, "orders/user/order_success.html", {"order": order, "payment": payment})


@login_required
@never_cache
def order_failure_view(request, order_number):
    """Order failure page — shown when Razorpay payment fails."""

    order = get_object_or_404(
        Order.objects.prefetch_related("payment"),
        user=request.user,
        order_number=order_number,
    )

    payment = get_payment_transaction(order)
    is_razorpay_failed = (
        order.status == "FAILED"
        and payment
        and payment.payment_method == "RAZORPAY"
    )

    return render(
        request,
        "orders/user/order_failure.html",
        {
            "order": order,
            "payment": payment,
            "is_razorpay_failed": is_razorpay_failed,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID if is_razorpay_failed else None,
        },
    )
