"""
Order calculation utilities — helper functions extracted from models.

Usage:
    from orders.utils import (
        get_payment_transaction,
        compute_item_totals,
        compute_cancel_refund,
        compute_return_refund,
        compute_coupon_share,
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


def compute_coupon_share(item):
    """
    Calculate proportional share of order's coupon discount for this item.
    Returns Decimal.
    """
    order = item.order
    if not order.coupon_discount or order.sub_total == 0:
        return Decimal("0.00")
    total_price = item.price * item.quantity
    share = (total_price / order.sub_total) * order.coupon_discount
    return share.quantize(Decimal("0.01"))


def compute_cancel_refund(item):
    """
    Full refund amount: item + shipping + tax, minus coupon share.
    Used when user cancels an item before shipping.
    """
    total_price = item.price * item.quantity
    coupon_share = compute_coupon_share(item)
    shipping_fee = Decimal(item.quantity * 100)
    taxable = total_price - coupon_share + shipping_fee
    tax = taxable * Decimal(settings.GST_RATE) / Decimal(100)
    return (taxable + tax).quantize(Decimal("0.01"))


def compute_return_refund(item):
    """
    Return refund amount: item + tax, minus coupon share. NO shipping refund.
    Used when a delivered item is returned.
    """
    total_price = item.price * item.quantity
    coupon_share = compute_coupon_share(item)
    taxable = total_price - coupon_share
    tax = taxable * Decimal(settings.GST_RATE) / Decimal(100)
    return (taxable + tax).quantize(Decimal("0.01"))


def can_return_item(order_item):
    """
    Check if an item is returnable:
    1. Status is DELIVERED
    2. Within 7 days of delivery
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
    return days_since <= 7
