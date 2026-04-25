"""
Background tasks for the orders app.
Uses Django's @task API with django-tasks-db backend.
"""

import logging
from django.conf import settings
from django.tasks import task
from orders.models import Order
from orders.service import change_order_status
from coupons.service import revoke_coupon_usage
from payments.models import Transaction
from users.cart.models import Cart, CartItem

logger = logging.getLogger(__name__)


@task
def expire_failed_order(order_id):
    """
    Auto-expire a FAILED or stale PENDING_PAYMENT Razorpay order.
    Enqueued at order creation — fires after FAILED_ORDER_EXPIRY_SECONDS.

    No-op if the order has already been paid, confirmed, or expired.

    Steps:
      1. Check order is still FAILED or PENDING_PAYMENT
      2. Restore cart items from snapshot (capped by MAX_QUANTITY_PURCHASE_PER_ITEM)
      3. Revoke coupon usage
      4. Cancel any PENDING/FAILED transactions (FAILED orders only)
      5. Transition order → EXPIRED
      6. Clear cart_snapshot and gateway_order_id
    """
    try:
        order = Order.objects.select_related("user", "coupon").get(pk=order_id)
    except Order.DoesNotExist:
        logger.warning("expire_failed_order: Order %s does not exist.", order_id)
        return

    # Only act on orders still awaiting payment or failed
    if order.status not in ("FAILED", "PENDING_PAYMENT"):
        logger.info(
            "expire_failed_order: Order %s is '%s' — skipping.",
            order.order_number,
            order.status,
        )
        return


    # 1. Restore cart items from snapshot
    if order.cart_snapshot and order.user:
        _restore_cart_from_snapshot(order.user, order.cart_snapshot)

    # 2. Revoke coupon usage
    if order.coupon:
        revoke_coupon_usage(order)

    # 3. Cancel lingering transactions (only for FAILED orders that
    #    went through a payment attempt — PENDING_PAYMENT orders
    #    have no transactions to cancel)
    if order.status == "FAILED":
        Transaction.objects.filter(
            content_type__model="order",
            object_id=order.pk,
        ).exclude(
            status__in=("PAID", "CANCELLED"),
        ).update(
            status="CANCELLED",
            note="Auto-cancelled: retry window expired",
        )

    # 4. Expire the order (PENDING_PAYMENT → EXPIRED or FAILED → EXPIRED)
    change_order_status(order=order, to_status="EXPIRED")

    # 5. Clear snapshot and gateway_order_id
    order.cart_snapshot = None
    order.gateway_order_id = ""
    order.save(update_fields=["cart_snapshot", "gateway_order_id"])

    logger.info(
        "expire_failed_order: Order %s expired successfully.", order.order_number
    )


def _restore_cart_from_snapshot(user, snapshot):
    """
    Re-add items from a cart_snapshot back into the user's cart.
    Quantities are capped at MAX_QUANTITY_PURCHASE_PER_ITEM.
    """
    max_qty = settings.MAX_QUANTITY_PURCHASE_PER_ITEM
    cart, _ = Cart.objects.get_or_create(user=user)

    for entry in snapshot:
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_variant_id=entry["variant_id"],
            defaults={"quantity": min(entry["quantity"], max_qty)},
        )
        if not created:
            cart_item.quantity = min(cart_item.quantity + entry["quantity"], max_qty)
            cart_item.save(update_fields=["quantity"])
