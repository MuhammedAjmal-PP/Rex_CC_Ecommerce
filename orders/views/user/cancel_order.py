from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from catalog.service import update_stock
from orders.models import Order, OrderItem
from orders.service import InvalidTransitionError, change_order_item_status
from orders.utils import compute_cancel_refund, get_payment_transaction
from coupons.service import revoke_coupon_if_invalid
from payments.service import complete_refund, initiate_refund, update_transaction


CANCELLABLE_ITEM_STATUSES = {"PENDING", "CONFIRMED", "PACKING", "READY"}


@login_required
@require_GET
@never_cache
def cancel_order(request, order_number):
    order = get_object_or_404(Order, user=request.user, order_number=order_number)

    # Only PLACED or CONFIRMED orders can be cancelled
    if order.status not in ("PLACED", "CONFIRMED"):
        messages.error(request, "This order cannot be cancelled.")
        return redirect("user_order_details", order_number=order.order_number)

    order_items = (
        OrderItem.objects.filter(order=order)
        .select_related(
            "product_variant",
            "product_variant__product",
            "product_variant__product__brand",
        )
        .prefetch_related("product_variant__images")
    )

    cancellable_items = [
        item for item in order_items if item.status in CANCELLABLE_ITEM_STATUSES
    ]

    context = {
        "order": order,
        "order_items": order_items,
        "cancellable_item_ids": {item.id for item in cancellable_items},
        "has_cancellable_items": bool(cancellable_items),
    }
    return render(request, "orders/user/cancel_order.html", context)


@login_required
@require_POST
@never_cache
def cancel_order_submit(request, order_number):
    order = get_object_or_404(Order, user=request.user, order_number=order_number)

    # Order status guard (L1 fix)
    if order.status not in ("PLACED", "CONFIRMED"):
        messages.error(request, "This order cannot be cancelled.")
        return redirect("user_order_details", order_number=order.order_number)

    selected_ids = request.POST.getlist("item_ids")
    reason_note = request.POST.get("reason_note", "").strip()

    if not selected_ids:
        messages.error(request, "Please select at least one item to cancel.")
        return redirect("user_cancel_order", order_number=order.order_number)

    if not reason_note:
        messages.error(request, "Please provide a reason for cancellation.")
        return redirect("user_cancel_order", order_number=order.order_number)

    selected_items = list(
        OrderItem.objects.filter(order=order, id__in=selected_ids).select_related(
            "product_variant", "product_variant__product"
        )
    )

    if len(selected_items) != len(set(selected_ids)):
        messages.error(request, "Invalid item selection. Please try again.")
        return redirect("user_cancel_order", order_number=order.order_number)

    note = f"Cancelled by user. Reason: {reason_note}"

    try:
        with transaction.atomic():
            cancelled_count = 0
            for item in selected_items:
                change_order_item_status(
                    order_item=item,
                    to_status="CANCELLED",
                )

                # Restore stock for the cancelled item
                update_stock(
                    product_variant=item.product_variant,
                    change=+item.quantity,
                    reason="ORDER_CANCELLED",
                    actor=request.user,
                    reference_object=item,
                    note=f"Stock restored — order {order.order_number} item cancelled",
                )

                # Refund logic: prepaid → wallet credit, COD → reduce pending amount
                payment = get_payment_transaction(order)
                cancel_amount = compute_cancel_refund(item)
                if payment and payment.payment_method != "COD":
                    refund_txn = initiate_refund(
                        order=order,
                        user=request.user,
                        amount=cancel_amount,
                        txn_type="CANCELLATION_REFUND",
                        content_object=item,
                        note=note,
                    )
                    complete_refund(
                        transaction=refund_txn,
                        wallet_reason="CANCELLATION_REFUND",
                    )
                elif payment:
                    update_transaction(
                        order=order,
                        amount=cancel_amount,
                        note="Adjusted for partial cancellation.",
                    )

                cancelled_count += 1

            # Revoke coupon if remaining items no longer qualify
            revoke_coupon_if_invalid(order)

    except InvalidTransitionError as error:
        messages.error(request, f"Unable to cancel selected item(s): {error}")
        return redirect("user_cancel_order", order_number=order.order_number)

    messages.success(
        request,
        f"{cancelled_count} item(s) cancelled. Refund processing status will be visible in your wallet.",
    )
    return redirect("user_order_details", order_number=order.order_number)
