"""
Order calculation utilities — helper functions extracted from models.

Usage:
    from orders.utils import (
        get_payment_transaction,
        compute_item_totals,
        compute_cancel_refund,
        compute_return_refund,
        can_generate_invoice,
        can_return_item,
    )
"""

from decimal import Decimal
from django.conf import settings
from django.utils import timezone

# ────────────────────────────────────────────
# Order helpers
# ────────────────────────────────────────────


def get_payment_transaction(order):
    """Return the primary ORDER_PAYMENT transaction for an order, or None."""
    return next(
        (txn for txn in order.payment.all() if txn.transaction_type == "ORDER_PAYMENT"),
        None,
    )


def can_generate_invoice(order):
    """Check if order status allows invoice generation."""
    return order.status in ("CONFIRMED", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED")


# ────────────────────────────────────────────
# OrderItem helpers
# ────────────────────────────────────────────


def compute_item_totals(item):
    """
    Compute price totals for an order item.
    Returns dict with total_price, total_original_price, item_discount.
    """
    total_price = item.price * item.quantity
    total_original = item.original_price * item.quantity
    discount = (item.original_price - item.price) * item.quantity
    return {
        "total_price": total_price,
        "total_original_price": total_original,
        "item_discount": discount,
    }


def _compute_order_total(items, order, include_shipping=True):
    """
    Calculate the grand total for a subset of order items.

    Steps:
        1. Sum item subtotal  (price × qty for each item)
        2. Calculate coupon discount for that subtotal
           — only if the coupon's min_order_amount is still met
        3. Add shipping  (qty × SHIPPING_CHARGE per item, if included)
        4. Apply GST on  (subtotal − coupon + shipping)
        5. Return dict with grand_total and coupon_discount

    Returns {"grand_total": Decimal("0.00"), "coupon_discount": Decimal("0.00")}
    when items is empty.
    """
    _ZERO = Decimal("0.00")
    if not items:
        return {"grand_total": _ZERO, "coupon_discount": _ZERO}

    subtotal = sum(i.price * i.quantity for i in items)
    shipping = Decimal("0.00")
    coupon_discount = Decimal("0.00")

    if include_shipping:
        shipping = sum(Decimal(i.quantity * settings.SHIPPING_CHARGE) for i in items)

    # Recalculate coupon discount for this subtotal
    coupon = order.coupon
    if coupon and not order.coupon_revoke:
        if subtotal >= coupon.min_order_amount:
            coupon_discount = coupon.calculate_discount(subtotal)

    taxable = subtotal - coupon_discount + shipping
    tax = (taxable * Decimal(settings.GST_RATE) / Decimal(100)).quantize(
        Decimal("0.01")
    )
    return {
        "grand_total": (taxable + tax).quantize(Decimal("0.01")),
        "coupon_discount": coupon_discount,
    }


# Statuses that are already "out" of the order
_TERMINAL_STATUSES = {"CANCELLED", "RETURNED"}


def compute_cancel_refund(item):
    """
    Cancel refund = before_total − after_total.

    before_total : grand total of all currently active items (including this one)
    after_total  : grand total of active items WITHOUT this one

    Shipping IS refunded (the item hasn't been shipped yet).
    Coupon discount is recalculated for the surviving items and
    automatically invalidated if the remaining subtotal drops
    below the coupon's min_order_amount.

    Returns:
        dict with refund_amount, discount_lost, coupon_discount_lost
    """
    order = item.order
    all_items = list(order.items.all())

    before_items = [i for i in all_items if i.status not in _TERMINAL_STATUSES]
    after_items = [i for i in before_items if i.id != item.id]

    before = _compute_order_total(before_items, order, include_shipping=True)
    after = _compute_order_total(after_items, order, include_shipping=True)

    refund = (before["grand_total"] - after["grand_total"]).quantize(Decimal("0.01"))
    coupon_lost = (
        before["coupon_discount"] - after["coupon_discount"]
    ).quantize(Decimal("0.01"))

    return {
        "refund_amount": max(refund, Decimal("0.00")),
        "discount_lost": ((item.original_price - item.price) * item.quantity).quantize(
            Decimal("0.01")
        ),
        "coupon_discount_lost": max(coupon_lost, Decimal("0.00")),
    }


def compute_return_refund(item):
    """
    Return refund = before_total − after_total.

    Same logic as cancel, but shipping is NOT refunded because the
    item was already delivered.  We keep shipping identical in both
    calculations so it cancels out in the difference.

    Returns:
        dict with refund_amount, discount_lost, coupon_discount_lost
    """
    order = item.order
    all_items = list(order.items.all())

    before_items = [i for i in all_items if i.status not in _TERMINAL_STATUSES]
    after_items = [i for i in before_items if i.id != item.id]

    # Use before_items for shipping in BOTH sides so shipping doesn't
    # appear in the refund difference.
    before = _compute_order_total(before_items, order, include_shipping=True)
    before_total = before["grand_total"]
    before_coupon = before["coupon_discount"]

    # After total: surviving items' subtotal/coupon, but shipping stays
    # the same as before (so it cancels out → no shipping refund).
    after_subtotal = sum(i.price * i.quantity for i in after_items)
    before_shipping = sum(
        Decimal(i.quantity * settings.SHIPPING_CHARGE) for i in before_items
    )

    after_coupon = Decimal("0.00")
    coupon = order.coupon
    if coupon and not order.coupon_revoke and after_items:
        if after_subtotal >= coupon.min_order_amount:
            after_coupon = coupon.calculate_discount(after_subtotal)

    after_taxable = after_subtotal - after_coupon + before_shipping
    after_tax = (after_taxable * Decimal(settings.GST_RATE) / Decimal(100)).quantize(
        Decimal("0.01")
    )
    after_total = (after_taxable + after_tax).quantize(Decimal("0.01"))

    refund = (before_total - after_total).quantize(Decimal("0.01"))
    coupon_lost = (before_coupon - after_coupon).quantize(Decimal("0.01"))

    return {
        "refund_amount": max(refund, Decimal("0.00")),
        "discount_lost": ((item.original_price - item.price) * item.quantity).quantize(
            Decimal("0.01")
        ),
        "coupon_discount_lost": max(coupon_lost, Decimal("0.00")),
    }


def can_return_item(order_item):
    """
    Check if an item is returnable:
    1. Status is DELIVERED
    2. Within RETURN_WINDOW_DAYS of delivery (configurable via env)
    3. No active return request exists
    """
    if order_item.status != "DELIVERED":
        return False

    # Check for existing return request
    try:
        existing = order_item.return_request
        if existing.status in ("REQUESTED", "APPROVED", "REJECTED"):
            return False
    except order_item.__class__.return_request.RelatedObjectDoesNotExist:
        pass

    days_since = (timezone.now() - order_item.status_updated_at).days
    return days_since <= settings.RETURN_WINDOW_DAYS
