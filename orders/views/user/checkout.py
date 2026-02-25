from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from users.cart.models import Cart
from users.cart.utils import build_cart_summary, fetch_cart
from users.user_profile.forms import AddressForm
from users.user_profile.models import Address
from users.wallet.service import get_or_create_wallet
from orders.service import (
    InsufficientStockError,
    build_unlocked_stock_lookup,
    validate_stock,
)


# Create your views here.


@login_required
@never_cache
def checkoutview(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect("user_cart")

    cart_items = fetch_cart(cart)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("user_cart")

    stock_lookup = build_unlocked_stock_lookup(items=cart_items)

    try:
        validate_stock(items=cart_items, stock_lookup=stock_lookup)
    except InsufficientStockError as error:
        messages.error(request, str(error))
        return redirect("user_cart")

    products = build_cart_summary(cart_items)

    addresses = Address.active.filter(user=request.user).order_by(
        "-is_default", "-updated_at"
    )
    can_add_address = addresses.count() < settings.MAX_ADDRESSES_PER_USER
    address_form = AddressForm() if can_add_address else None

    order_summary = {
        "items_count": cart.items_count,
        "mrp_total": cart.total,
        "discount": cart.discount,
        "sub_total": cart.sub_total,
        "shipping_charge": cart.shipping_fee,
        "gst_rate": settings.GST_RATE,
        "tax": cart.tax,
        "grand_total": cart.grand_total,
    }

    # ── Coupon ──────────────────────────────────────────
    applied_coupon = request.session.get("applied_coupon")
    coupon_discount = Decimal("0.00")
    if applied_coupon:
        coupon_discount = Decimal(applied_coupon.get("discount_amount", "0.00"))
        order_summary["coupon_code"] = applied_coupon["code"]
        order_summary["coupon_discount"] = coupon_discount
        # Recalculate: sub_total → coupon → shipping → tax → grand_total
        adjusted_sub = max(order_summary["sub_total"] - coupon_discount, Decimal("0.00"))
        adjusted_total_amount = adjusted_sub + order_summary["shipping_charge"]
        adjusted_tax = (adjusted_total_amount * Decimal(settings.GST_RATE) / Decimal("100")).quantize(Decimal("0.01"))
        order_summary["tax"] = adjusted_tax
        order_summary["grand_total"] = adjusted_total_amount + adjusted_tax

    # Fetch coupons the user can potentially use
    from coupons.models import Coupon as CouponModel
    from coupons.models import CouponUsage
    from django.utils import timezone
    from django.db.models import Count

    now = timezone.now()

    # Only exclude coupons where user has reached per_user_limit
    user_usage = (
        CouponUsage.objects.filter(user=request.user)
        .values("coupon_id")
        .annotate(usage_count=Count("id"))
    )
    exhausted_ids = set()
    for entry in user_usage:
        try:
            coupon = CouponModel.objects.get(pk=entry["coupon_id"])
            if entry["usage_count"] >= coupon.per_user_limit:
                exhausted_ids.add(coupon.pk)
        except CouponModel.DoesNotExist:
            pass

    available_coupons = (
        CouponModel.active.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
        )
        .exclude(pk__in=exhausted_ids)
        .order_by("-discount_value")[:5]
    )
    # ───────────────────────────────────────────────────

    wallet = get_or_create_wallet(request.user)

    context = {
        "items": products,
        "order_summary": order_summary,
        "addresses": addresses,
        "can_add_address": can_add_address,
        "address_form": address_form,
        "wallet_balance": wallet.balance,
        "applied_coupon": applied_coupon,
        "available_coupons": available_coupons,
    }

    return render(request, "orders/user/checkout/checkout.html", context)


@login_required
@require_GET
@never_cache
def get_addresses(request):
    """is for checkout address section"""
    addresses = Address.active.filter(user=request.user).order_by(
        "-is_default", "-updated_at"
    )
    can_add_address = addresses.count() < settings.MAX_ADDRESSES_PER_USER
    address_form = AddressForm()

    context = {
        "addresses": addresses,
        "address_form": address_form,
        "can_add_address": can_add_address,
    }

    return render(
        request, "orders/user/checkout/partials/address_section.html", context
    )
