from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from users.cart.models import Cart
from users.cart.utils import build_cart_summary, compute_cart_summary, fetch_cart
from users.user_profile.forms import AddressForm
from users.user_profile.models import Address
from users.wallet.service import get_or_create_wallet
from orders.service import (
    InsufficientStockError,
    build_unlocked_stock_lookup,
    validate_stock,
)
from coupons.models import Coupon as CouponModel
from coupons.service import get_exhausted_coupon_ids
from django.utils import timezone
from django.db.models import Count

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

    # Use utility for totals
    summary = compute_cart_summary(cart, cart_items=list(cart_items))

    order_summary = {
        "items_count": summary["items_count"],
        "mrp_total": summary["total"],
        "discount": summary["discount"],
        "sub_total": summary["sub_total"],
        "shipping_charge": summary["shipping_fee"],
        "gst_rate": settings.GST_RATE,
        "tax": summary["tax"],
        "grand_total": summary["grand_total"],
    }

    # ── Coupon: clear any stale session coupon on fresh checkout load ──
    if "applied_coupon" in request.session:
        del request.session["applied_coupon"]

    now = timezone.now()

    exhausted_ids = get_exhausted_coupon_ids(request.user)

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
        "available_coupons": available_coupons,
        "cod_limit": settings.COD_MIN_ORDER_AMOUNT,
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
