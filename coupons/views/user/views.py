"""
User-facing AJAX endpoints for applying/removing coupons at checkout.
Coupon state is stored in request.session['applied_coupon'].
"""

import json
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from users.cart.models import Cart
from users.cart.utils import compute_cart_summary
from coupons.service import InvalidCouponError, validate_coupon


@login_required
@require_POST
def apply_coupon(request):
    """
    Validate and apply a coupon code to the current session.
    Returns JSON with discount info for frontend display.
    """
    try:
        body = json.loads(request.body)
        code = body.get("code", "").strip()
    except (json.JSONDecodeError, AttributeError):
        code = request.POST.get("code", "").strip()

    if not code:
        return JsonResponse({"success": False, "message": "Please enter a coupon code."}, status=400)

    # Get cart subtotal
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({"success": False, "message": "Your cart is empty."}, status=400)

    summary = compute_cart_summary(cart)

    try:
        coupon, discount_amount = validate_coupon(code, request.user, summary["sub_total"])
    except InvalidCouponError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

    # Recalculate totals: sub_total → coupon → shipping → tax → grand_total
    adjusted_sub = max(summary["sub_total"] - discount_amount, Decimal("0.00"))
    adjusted_total_amount = adjusted_sub + summary["shipping_fee"]
    adjusted_tax = (adjusted_total_amount * Decimal(settings.GST_RATE) / Decimal("100")).quantize(Decimal("0.01"))
    new_grand_total = adjusted_total_amount + adjusted_tax

    # Store in session
    request.session["applied_coupon"] = {
        "code": coupon.code,
        "coupon_id": coupon.pk,
        "discount_amount": str(discount_amount),
        "description": coupon.description or f"{coupon.discount_value}% off"
        if coupon.discount_type == "PERCENTAGE"
        else f"₹{coupon.discount_value} off",
    }

    return JsonResponse({
        "success": True,
        "message": f"Coupon '{coupon.code}' applied!",
        "coupon_code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": str(coupon.discount_value),
        "discount_amount": str(discount_amount),
        "new_grand_total": str(new_grand_total),
        "description": request.session["applied_coupon"]["description"],
    })


@login_required
@require_POST
def remove_coupon(request):
    """Remove the applied coupon from the session."""
    if "applied_coupon" in request.session:
        del request.session["applied_coupon"]
        request.session.modified = True

    # Return original totals
    try:
        cart = Cart.objects.get(user=request.user)
        summary = compute_cart_summary(cart)
        grand_total = str(summary["grand_total"])
    except Cart.DoesNotExist:
        grand_total = "0.00"

    return JsonResponse({
        "success": True,
        "message": "Coupon removed.",
        "grand_total": grand_total,
    })
