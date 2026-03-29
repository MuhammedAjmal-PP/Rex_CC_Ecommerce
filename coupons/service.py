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
    return _validate(code, user, cart_subtotal, lock=False)


def validate_coupon_locked(code, user, cart_subtotal):
    """
    Same as validate_coupon but locks the coupon row with SELECT ... FOR UPDATE.
    Must be called inside transaction.atomic() to prevent race conditions
    (e.g. two users claiming the last usage slot).

    Returns:
        (coupon, discount_amount) on success.

    Raises:
        InvalidCouponError with a user-friendly message.
    """
    return _validate(code, user, cart_subtotal, lock=True)


def _validate(code, user, cart_subtotal, lock=False):
    """Internal validation logic shared by locked and unlocked paths."""
    code = code.strip().upper()
    cart_subtotal = Decimal(str(cart_subtotal))

    # 1. Does it exist?
    try:
        qs = Coupon.objects.select_for_update() if lock else Coupon.objects
        coupon = qs.get(code=code)
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

    # 4. Per-user limit
    user_usage_count = CouponUsage.objects.filter(coupon=coupon, user=user).count()
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


# Terminal item statuses — items no longer "active" in the order
_TERMINAL_STATUSES = {"CANCELLED", "RETURNED"}


def revoke_coupon_if_invalid(order):
    """
    Check whether the order's coupon is still valid for the remaining
    active items.  If not (all items gone, or subtotal below
    min_order_amount), revoke the coupon usage so the user can reuse it.

    Should be called inside a transaction.atomic() block after
    cancelling or completing a return.
    """
    if not order.coupon or not order.coupon_discount:
        return

    remaining = [i for i in order.items.all() if i.status not in _TERMINAL_STATUSES]
    remaining_subtotal = sum(i.price * i.quantity for i in remaining)
    all_gone = len(remaining) == 0
    below_min = remaining_subtotal < order.coupon.min_order_amount

    if all_gone or below_min:
        revoke_coupon_usage(order)
        order.coupon_revoke = True
        order.save(update_fields=["coupon_revoke"])
        # order.coupon_discount = 0
        # order.save(update_fields=["coupon_discount"])


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
        for c in Coupon.objects.filter(pk__in=coupon_id_list).only(
            "pk", "per_user_limit"
        )
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
