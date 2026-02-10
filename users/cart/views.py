from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from catalog.models import Product, ProductVariant
from users.cart.models import Cart, CartItem
from users.cart.utils import build_cart_summary, fetch_cart
from users.wishlist.models import Wishlist, WishlistItem

# Create your views here.


@login_required
@never_cache
def view_cart(request):
    """Get or create cart for the user"""

    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_items = fetch_cart(cart)

    products = build_cart_summary(cart_items)

    # order summay variables
    total_discount = Decimal("0.00")

    order_summary = {
        "products_count": cart.items_count,
        "sub_total": cart.sub_total,
        "total_discount": total_discount,
        "shipping_fee": cart.shipping_fee,
        "total_amount_to_pay": cart.total_amount,
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

    # Parse quantity safely
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        return JsonResponse(
            {"success": False, "message": "Invalid quantity"},
            status=400,
        )

    # Validate quantity
    if quantity <= 0:
        return JsonResponse(
            {"success": False, "message": "Quantity must be greater than zero"},
            status=400,
        )

    # Get existing cart item (without quantity)
    cart_item = CartItem.objects.filter(cart=cart, product_variant=variant).first()

    # Compute merged quantity
    if cart_item:
        new_quantity = cart_item.quantity + quantity
    else:
        new_quantity = quantity

    # Stock validation
    if new_quantity > variant.stock:
        return JsonResponse(
            {
                "success": False,
                "message": f"Only {variant.stock} item(s) available",
            },
            status=400,
        )

    # Save
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
        }
    )


@login_required
@require_POST
def update_cart(request, slug, sku):
    """
    Update or remove a cart item.
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

    remove = request.POST.get("remove") == "true"

    if remove or quantity <= 0:
        cart_item.delete()
        return redirect("user_cart")

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

    return redirect("user_cart")


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
