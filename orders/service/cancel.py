"""
Shared cancellation logic — used by both user and admin cancel flows.

Usage:
    from orders.service.cancel import cancel_order_item, cancel_order_items
"""

from django.db import transaction

from catalog.service import update_stock
from coupons.service import revoke_coupon_if_invalid
from orders.service.status import InvalidTransitionError, change_order_item_status
from orders.utils import compute_cancel_refund, get_payment_transaction
from payments.service import complete_refund, initiate_refund, update_transaction


# Statuses that can still be cancelled
CANCELLABLE_STATUSES = {"PENDING", "CONFIRMED", "PACKING", "READY"}


def cancel_order_item(*, order_item, actor, note="", auto_complete_refund=True):
    """
    Cancel a single order item with all side-effects.

    IMPORTANT: This must be called inside a transaction.atomic() block
    when cancelling multiple items to ensure consistency.

    Steps:
      1. Compute refund BEFORE status change (uses active items for calculation)
      2. Change item status → CANCELLED
      3. Restore stock
      4. Handle refund (prepaid → wallet, COD → reduce pending amount)
      5. Update analytics trackers on order

    Args:
        order_item: The OrderItem to cancel.
        actor: The user performing the action (for stock audit trail).
        note: Reason for cancellation.
        auto_complete_refund: If True, immediately credit wallet for prepaid
            refunds. If False, create PENDING refund for admin approval.

    Returns:
        dict with refund_amount, discount_lost, coupon_discount_lost
    """
    order = order_item.order

    # 1. Compute refund BEFORE status change
    refund_info = compute_cancel_refund(order_item)
    cancel_amount = refund_info["refund_amount"]

    # 2. Change item status → CANCELLED
    change_order_item_status(order_item=order_item, to_status="CANCELLED")

    # 3. Restore stock
    update_stock(
        product_variant=order_item.product_variant,
        change=+order_item.quantity,
        reason="ORDER_CANCELLED",
        actor=actor,
        reference_object=order_item,
        note=note or f"Stock restored — order {order.order_number} item cancelled",
    )

    # 4. Handle refund
    payment = get_payment_transaction(order)
    if payment and payment.payment_method != "COD" and payment.status == "PAID":
        # Prepaid (Razorpay / Wallet) — create refund transaction
        refund_txn = initiate_refund(
            order=order,
            user=order.user,
            amount=cancel_amount,
            txn_type="CANCELLATION_REFUND",
            content_object=order_item,
            note=note or f"Cancellation refund — order {order.order_number}",
        )
        if auto_complete_refund:
            complete_refund(transaction=refund_txn)
    elif payment and payment.payment_method == "COD":
        # COD — reduce pending amount
        update_transaction(
            order=order,
            amount=cancel_amount,
            note=note or "Adjusted for cancellation.",
        )

    # 5. Update analytics trackers
    order.refunded_amount += refund_info["refund_amount"]
    order.refunded_discount += refund_info["discount_lost"]
    order.refunded_coupon_discount += refund_info["coupon_discount_lost"]

    return refund_info


def cancel_order_items(*, order, items, actor, note="", auto_complete_refund=True):
    """
    Cancel multiple items in an atomic block.

    After all items are cancelled:
      - Persist accumulated analytics trackers on the order
      - Revoke coupon if remaining items no longer qualify

    Args:
        order: The Order instance.
        items: List of OrderItem instances to cancel.
        actor: The user performing the action.
        note: Reason for cancellation.
        auto_complete_refund: If True, immediately credit wallet for prepaid
            refunds. If False, create PENDING refund for admin approval.

    Returns:
        int — count of successfully cancelled items
    """
    cancelled_count = 0

    with transaction.atomic():
        for item in items:
            if item.status not in CANCELLABLE_STATUSES:
                continue

            cancel_order_item(
                order_item=item,
                actor=actor,
                note=note,
                auto_complete_refund=auto_complete_refund,
            )
            cancelled_count += 1

        # Persist analytics trackers (accumulated by cancel_order_item calls)
        if cancelled_count > 0:
            order.save(
                update_fields=[
                    "refunded_amount",
                    "refunded_discount",
                    "refunded_coupon_discount",
                ]
            )

            # Revoke coupon if remaining items no longer qualify
            revoke_coupon_if_invalid(order)

    return cancelled_count
