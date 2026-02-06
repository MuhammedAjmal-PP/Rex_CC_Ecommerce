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

    products, products_total_price = build_cart_summary(cart_items)

    addresses = Address.active.filter(user=request.user).order_by(
        "-is_default", "-updated_at"
    )
    can_add_address = addresses.count() < settings.MAX_ADDRESSES_PER_USER
    address_form = AddressForm() if can_add_address else None

    subtotal = products_total_price
    tax = (subtotal * Decimal("18")) / Decimal("100")
    discount = Decimal("0")
    shipping_charge = sum(Decimal("100") * item.quantity for item in cart_items)
    total = subtotal + tax + shipping_charge - discount

    order_summary = {
        "items_count": len(products),
        "subtotal": subtotal,
        "discount": discount,
        "shipping_charge": shipping_charge,
        "total": total,
    }

    context = {
        "items": products,
        "order_summary": order_summary,
        "addresses": addresses,
        "can_add_address": can_add_address,
        "address_form": address_form,
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
