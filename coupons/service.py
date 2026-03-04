"""
Coupon validation, application, and revocation service.
"""

from decimal import Decimal
from django.db.models import Count, F
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

    # 1. Does it exist? select_for_update prevents race conditions (fix #18)
    # Note: caller must be inside transaction.atomic() — place_order already does this
    try:
        coupon = Coupon.objects.select_for_update().get(code=code)
    except Coupon.DoesNotExist:
        raise InvalidCouponError("Invalid coupon code.")

    # 2. Soft-deleted?
    if coupon.is_deleted:
        raise InvalidCouponError("Invalid coupon code.")

    # 3. Is it active & within dates?
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


# ────────────────────────────────────────────
# Query helpers
# ────────────────────────────────────────────


def get_exhausted_coupon_ids(user):
    """
    Return a set of coupon PKs that the given user can no longer use
    because they have reached the per-user usage limit.

    Uses a single bulk query instead of a per-coupon get() in a loop.
    """
    user_usage = (
        CouponUsage.objects.filter(user=user)
        .values("coupon_id")
        .annotate(usage_count=Count("id"))
    )

    if not user_usage:
        return set()

    coupon_id_list = [e["coupon_id"] for e in user_usage]
    usage_map = {e["coupon_id"]: e["usage_count"] for e in user_usage}
    limits = {
        c.pk: c.per_user_limit
        for c in Coupon.objects.filter(pk__in=coupon_id_list).only("pk", "per_user_limit")
    }
    return {cid for cid, limit in limits.items() if usage_map.get(cid, 0) >= limit}


# ────────────────────────────────────────────
# Recalculate totals with coupon discount
# ────────────────────────────────────────────


def recalculate_with_coupon(sub_total, shipping_fee, gst_rate, coupon_discount):
    """
    Apply coupon discount and recalculate:
        sub_total → coupon → shipping → tax → grand_total

    Returns:
        dict with adjusted_sub, shipping_fee, tax, grand_total
    """
    adjusted_sub = max(sub_total - coupon_discount, Decimal("0.00"))
    total_before_tax = adjusted_sub + shipping_fee
    tax = (total_before_tax * Decimal(str(gst_rate)) / Decimal("100")).quantize(
        Decimal("0.01")
    )
    grand_total = total_before_tax + tax

    return {
        "adjusted_sub": adjusted_sub,
        "shipping_fee": shipping_fee,
        "tax": tax,
        "grand_total": grand_total,
    }

