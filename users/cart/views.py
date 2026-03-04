from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from catalog.models import Product, ProductVariant
from catalog.utils import pack_variants
from users.cart.models import Cart, CartItem
from users.cart.utils import (
    build_cart_summary,
    compute_cart_summary,
    fetch_cart,
    summary_to_json,
)
from users.wishlist.models import Wishlist, WishlistItem


@login_required
@never_cache
def view_cart(request):
    """Get or create cart for the user"""

    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_items = fetch_cart(cart)

    products = build_cart_summary(cart_items)

    summary = compute_cart_summary(cart)

    order_summary = {
        "products_count": summary["items_count"],
        "total": summary["total"],
        "discount": summary["discount"],
        "sub_total": summary["sub_total"],
        "shipping_fee": summary["shipping_fee"],
        "total_amount_to_pay": summary["total_amount"],
    }

    context = {
        "items": products,
        "order_summary": order_summary,
    }

    return render(request, "cart/cart.html", context)


@login_required
@require_POST
def add_cart(request, slug, sku):
    """
    Add a product variant to the user's cart.

    - Accepts quantity from product detail or wishlist
    - Merges quantity if item already exists in cart
    - Validates stock before saving
    - Removes item from wishlist if present
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)

    product = get_object_or_404(Product, slug=slug, is_drafted=False, is_deleted=False)

    variant = get_object_or_404(
        ProductVariant,
        product=product,
        sku=sku,
        is_drafted=False,
        is_deleted=False,
    )

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        return JsonResponse(
            {"success": False, "message": "Invalid quantity"},
            status=400,
        )

    if quantity <= 0:
        return JsonResponse(
            {"success": False, "message": "Quantity must be greater than zero"},
            status=400,
        )

    cart_item = CartItem.objects.filter(cart=cart, product_variant=variant).first()

    if cart_item:
        new_quantity = cart_item.quantity + quantity
    else:
        new_quantity = quantity

    if new_quantity > settings.MAX_QUANTITY_PURCHASE_PER_ITEM:
        return JsonResponse(
            {
                "success": False,
                "message": f"You can purchase a maximum of {settings.MAX_QUANTITY_PURCHASE_PER_ITEM} units of this item per order.",
            },
            status=400,
        )

    if new_quantity > variant.stock:
        return JsonResponse(
            {
                "success": False,
                "message": f"Only {variant.stock} item(s) available",
            },
            status=400,
        )

    if cart_item:
        cart_item.quantity = new_quantity
        cart_item.save()
        message = "Cart quantity updated"
    else:
        CartItem.objects.create(
            cart=cart,
            product_variant=variant,
            quantity=new_quantity,
        )
        message = "Added to cart"

    # Enforce cart > wishlist
    wishlist = Wishlist.objects.filter(user=request.user).first()
    if wishlist:
        WishlistItem.objects.filter(
            wishlist=wishlist,
            product_variant=variant,
        ).delete()

    return JsonResponse(
        {
            "success": True,
            "message": message,
            "added": True,
            "quantity": new_quantity,
            "cart_count": cart.items_count,
        }
    )


@login_required
@require_POST
def update_cart_quantity(request, slug, sku):
    """
    Update quantity of a cart item (increment / decrement).
    Returns JSON with updated item data and order summary.
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)

    product = get_object_or_404(Product, slug=slug, is_drafted=False, is_deleted=False)
    variant = get_object_or_404(
        ProductVariant,
        product=product,
        sku=sku,
        is_drafted=False,
        is_deleted=False,
    )
    cart_item = get_object_or_404(CartItem, cart=cart, product_variant=variant)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        return JsonResponse(
            {"success": False, "message": "Invalid quantity"},
            status=400,
        )

    if quantity <= 0:
        return JsonResponse(
            {"success": False, "message": "Quantity must be at least 1"},
            status=400,
        )

    if quantity > settings.MAX_QUANTITY_PURCHASE_PER_ITEM:
        return JsonResponse(
            {
                "success": False,
                "message": f"You can purchase a maximum of {settings.MAX_QUANTITY_PURCHASE_PER_ITEM} units of this item per order.",
            },
            status=400,
        )

    if quantity > variant.stock:
        return JsonResponse(
            {
                "success": False,
                "message": f"Only {variant.stock} item(s) available",
            },
            status=400,
        )

    cart_item.quantity = quantity
    cart_item.save(update_fields=["quantity"])

    # Pack the single variant for price data
    pack_variants([variant])

    allowed_max = min(variant.stock, settings.MAX_QUANTITY_PURCHASE_PER_ITEM)
    summary = compute_cart_summary(cart)

    return JsonResponse(
        {
            "success": True,
            "item": {
                "quantity": quantity,
                "total_amount": float(variant.final_price * quantity),
                "final_price": float(variant.final_price),
                "price": float(variant.price),
                "stock": variant.stock,
                "allowed_max": allowed_max,
                "is_in_stock": variant.stock > 0,
            },
            "order_summary": summary_to_json(summary),
        }
    )


@login_required
@require_POST
def remove_cart_item(request, slug, sku):
    """
    Remove a cart item entirely.
    Returns JSON with updated order summary and cart count.
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)

    product = get_object_or_404(Product, slug=slug, is_drafted=False, is_deleted=False)
    variant = get_object_or_404(
        ProductVariant,
        product=product,
        sku=sku,
        is_drafted=False,
        is_deleted=False,
    )
    cart_item = get_object_or_404(CartItem, cart=cart, product_variant=variant)

    cart_item.delete()

    summary = compute_cart_summary(cart)

    return JsonResponse(
        {
            "success": True,
            "removed": True,
            "cart_count": summary["items_count"],
            "order_summary": summary_to_json(summary),
        }
    )


@require_GET
def get_variant_stock(request, slug, sku):
    product = get_object_or_404(Product, slug=slug, is_drafted=False, is_deleted=False)
    variant = get_object_or_404(
        ProductVariant, product=product, sku=sku, is_drafted=False, is_deleted=False
    )
    return JsonResponse({"stock": variant.stock})


@require_GET
def get_cartitems_count(request):
    """
    API to fetch current cart count.
    Returns 0 if user is not authenticated or has no cart.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"cart_count": 0})

    cart, _ = Cart.objects.get_or_create(user=request.user)

    return JsonResponse({"cart_count": cart.items_count})
