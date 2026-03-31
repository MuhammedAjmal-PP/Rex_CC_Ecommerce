"""
Order placement helpers — business logic used by place_order and razorpay views.
"""
from datetime import timedelta
from decimal import Decimal
from functools import partial
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from catalog.service import update_stock
from orders.models import OrderItem
from orders.service.stock import validate_snapshot_stock
from orders.tasks import expire_failed_order


def schedule_order_expiry(order):
    """
    Schedule an auto-expiry task for a failed/pending Razorpay order.

    Uses `transaction.on_commit` so the task is only enqueued after the
    current DB transaction commits successfully.  The task itself is a
    no-op if the order is no longer FAILED when it runs.
    """
    transaction.on_commit(
        partial(
            expire_failed_order.using(
                run_after=timezone.now() + timedelta(seconds=settings.FAILED_ORDER_EXPIRY_SECONDS)
            ).enqueue,
            order_id=order.pk,
        )
    )


def build_cart_snapshot(cart_items, packed_prices, locked_variants):
    """
    Build a JSON-serialisable snapshot of the cart.
    Saved on the Order so items can be created later (after Razorpay payment).

    Returns a list like:
    [
        {"variant_id": 42, "quantity": 2, "price": "999.00", "original_price": "1299.00"},
        ...
    ]
    """
    snapshot = []
    for item in cart_items:
        vid = item.product_variant_id
        locked = locked_variants[vid]
        snapshot.append({
            "variant_id": vid,
            "quantity": item.quantity,
            "price": str(packed_prices.get(vid, locked.price)),
            "original_price": str(locked.price),
        })
    return snapshot


def create_items_from_snapshot(order, snapshot, actor):
    """
    Create OrderItems and deduct stock from a saved cart_snapshot.
    Used by the Razorpay callback after payment is verified.

    Steps:
      1. Lock variants and validate stock (SELECT FOR UPDATE)
      2. Create OrderItem records
      3. Deduct stock for each item
    """
    # 1. Lock + validate (raises InsufficientStockError if out of stock)
    locked_variants = validate_snapshot_stock(snapshot)

    # 2 & 3. Create items and deduct stock
    for entry in snapshot:
        variant = locked_variants[entry["variant_id"]]

        order_item = OrderItem.objects.create(
            order=order,
            product_variant=variant,
            quantity=entry["quantity"],
            price=Decimal(entry["price"]),
            original_price=Decimal(entry["original_price"]),
        )

        update_stock(
            product_variant=variant,
            change=-entry["quantity"],
            reason="ORDER_PLACED",
            actor=actor,
            reference_object=order_item,
            note=f"Order {order.order_number} placed",
        )
