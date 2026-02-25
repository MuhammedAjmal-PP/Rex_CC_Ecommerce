"""
Coupon validation, application, and revocation service.
"""

from decimal import Decimal
from django.db.models import F
from coupons.models import Coupon, CouponUsage


class CouponError(Exception):
    """Base exception for coupon-related errors."""


class InvalidCouponError(CouponError):
    """Raised when a coupon code is invalid or cannot be applied."""


# ────────────────────────────────────────────
# Validate
# ────────────────────────────────────────────


def validate_coupon(code, user, cart_subtotal):
    """
    Validate a coupon code for a given user and cart subtotal.

    Returns:
        (coupon, discount_amount) on success.

    Raises:
        InvalidCouponError with a user-friendly message.
    """
    code = code.strip().upper()
    cart_subtotal = Decimal(str(cart_subtotal))

    # 1. Does it exist?
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        raise InvalidCouponError("Invalid coupon code.")

    # 2. Is it active & within dates?
    if not coupon.is_valid:
        if coupon.is_expired:
            raise InvalidCouponError("This coupon has expired.")
        raise InvalidCouponError("This coupon is not currently active.")

    # 3. Overall usage limit
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise InvalidCouponError("This coupon has reached its usage limit.")

    # 4. Per-user limit
    user_usage_count = CouponUsage.objects.filter(
        coupon=coupon, user=user
    ).count()
    if user_usage_count >= coupon.per_user_limit:
        raise InvalidCouponError("You have already used this coupon.")

    # 5. Minimum order amount
    if cart_subtotal < coupon.min_order_amount:
        raise InvalidCouponError(
            f"Minimum order of ₹{coupon.min_order_amount:,.2f} required for this coupon."
        )

    # 6. Calculate discount
    discount_amount = coupon.calculate_discount(cart_subtotal)

    if discount_amount <= 0:
        raise InvalidCouponError("This coupon does not apply to your order.")

    return coupon, discount_amount


# ────────────────────────────────────────────
# Apply (after order placement)
# ────────────────────────────────────────────


def apply_coupon_to_order(coupon, user, order):
    """
    Record the coupon usage after a successful order placement.
    Increments the coupon's used_count.
    """
    CouponUsage.objects.create(
        coupon=coupon,
        user=user,
        order=order,
    )
    Coupon.objects.filter(pk=coupon.pk).update(used_count=F("used_count") + 1)


# ────────────────────────────────────────────
# Revoke (on full order cancellation)
# ────────────────────────────────────────────


def revoke_coupon_usage(order):
    """
    Revoke a coupon usage for a fully-cancelled order.
    Decrements the coupon's used_count and deletes the usage record.
    """
    usage = CouponUsage.objects.filter(order=order).select_related("coupon").first()
    if not usage:
        return

    coupon = usage.coupon
    usage.delete()
    Coupon.objects.filter(pk=coupon.pk, used_count__gt=0).update(
        used_count=F("used_count") - 1
    )
