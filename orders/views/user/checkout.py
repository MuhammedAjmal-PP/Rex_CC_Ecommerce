from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from users.cart.models import Cart, CartItem
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

    cart_items = (
        CartItem.objects.filter(
            cart=cart,
            product_variant__is_deleted=False,
            product_variant__is_drafted=False,
            product_variant__product__is_deleted=False,
            product_variant__product__is_drafted=False,
        )
        .select_related(
            "product_variant",
            "product_variant__product",
            "product_variant__product__brand",
        )
        .prefetch_related("product_variant__images")
    )

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("user_cart")

    addresses = Address.active.filter(user=request.user).order_by(
        "-is_default", "-updated_at"
    )
    can_add_address = addresses.count() < settings.MAX_ADDRESSES_PER_USER
    address_form = AddressForm() if can_add_address else None

    subtotal = sum(
        item.product_variant.final_price * item.quantity for item in cart_items
    )
    tax = (subtotal * Decimal("18")) / Decimal("100")
    discount = Decimal("0")
    shipping_charge = sum(Decimal("100") * item.quantity for item in cart_items)
    total = subtotal + tax + shipping_charge - discount
    context = {
        "cart_items": cart_items,
        "addresses": addresses,
        "can_add_address": can_add_address,
        "address_form": address_form,
        "subtotal": subtotal,
        "tax": tax,
        "discount": discount,
        "shipping_charge": shipping_charge,
        "total": total,
    }

    return render(request, "orders/user/checkout.html", context)


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

    return render(request, "orders/user/partials/address_section.html", context)
