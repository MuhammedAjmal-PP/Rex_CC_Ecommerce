from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from catalog.models import Product, ProductVariant
from users.cart.models import Cart, CartItem
from users.wishlist.models import Wishlist, WishlistItem

# Create your views here.


@login_required
@never_cache
def view_cart(request):
    """Get or create cart for the user"""

    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_items = (
        CartItem.objects.filter(
            cart=cart,
            product_variant__is_deleted=False,
            product_variant__product__is_deleted=False,
        )
        .select_related(
            "product_variant",
            "product_variant__product",
            "product_variant__product__brand",
        )
        .prefetch_related("product_variant__images")
    )

    products = []
    products_total_price = Decimal("0.00")
    total_discount = Decimal("0.00")

    for item in cart_items:
        variant = item.product_variant
        image = variant.images.filter(is_primary=True).first()
        available = not variant.is_drafted and not variant.product.is_drafted

        products.append(
            {
                "variant": {
                    "id": variant.id,
                    "sku": variant.sku,
                    "slug": variant.product.slug,
                    "product_name": variant.product.name,
                    "brand": variant.product.brand.name,
                    "price": variant.price,
                    "final_price": variant.final_price,
                    "available": available,
                    "stock": variant.stock,
                    "is_in_stock": variant.stock > 0,
                    "image": image.image.url,
                },
                "quantity": item.quantity,
                "total_amount": variant.final_price * item.quantity,
                "total_discount": variant.discount_amount * item.quantity,
            }
        )
        products_total_price += variant.final_price * item.quantity
        total_discount += variant.discount_amount * item.quantity

    # order summay variables
    total_quantity = sum(item.quantity for item in cart_items)
    delivery_charge = Decimal("100.00") * total_quantity
    total_amount_to_pay = products_total_price + delivery_charge

    order_summary = {
        "products_count": len(products),
        "products_total_price": products_total_price,
        "total_discount": total_discount,
        "delivery_charge": delivery_charge,
        "total_amount_to_pay": total_amount_to_pay,
    }

    context = {
        "items": products,
        "order_summary": order_summary,
    }

    return render(request, "cart/cart.html", context)


@login_required
@require_POST
def add_cart(request, slug, sku):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, slug=slug, is_drafted=False, is_deleted=False)
    variant = get_object_or_404(
        ProductVariant, product=product, sku=sku, is_drafted=False, is_deleted=False
    )

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product_variant=variant,
    )
    if created:
        message = "Added to Cart"
        added = True
    else:
        cart_item.quantity += 1
        cart_item.save()
        message = "Incremented the product quantity"
        added = True

    wishlist = Wishlist.objects.get_or_create(user=request.user)
    wishlist_item = WishlistItem.objects.filter(
        wishlist=wishlist,
        product_variant=variant,
    ).first()

    if wishlist_item:
        wishlist_item.delete()

    return JsonResponse(
        {
            "success": True,
            "message": message,
            "added": added,
        }
    )


@login_required
@require_POST
def update_cart(request, slug, sku):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, slug=slug, is_drafted=False, is_deleted=False)
    variant = get_object_or_404(
        ProductVariant, product=product, sku=sku, is_drafted=False, is_deleted=False
    )
    cart_item = get_object_or_404(CartItem, cart=cart, product_variant=variant)

    try:
        quantity = int(request.POST.get("quantity", 0))
        remove = request.POST.get("remove") == "true"
    except ValueError:
        return JsonResponse({"error": "Invalid quantity"}, status=400)

    if remove:
        cart_item.delete()
        return redirect("user_cart")

    if quantity <= 0:
        cart_item.delete()
        return redirect("user_cart")

    if quantity > variant.stock:
        return JsonResponse(
            {
                "error": "Insufficient stock",
            },
            status=400,
        )

    cart_item.quantity = quantity
    cart_item.save()
    return redirect("user_cart")


@login_required
@require_GET
def get_variant_stock(request, slug, sku):
    product = get_object_or_404(Product, slug=slug, is_drafted=False, is_deleted=False)
    variant = get_object_or_404(
        ProductVariant, product=product, sku=sku, is_drafted=False, is_deleted=False
    )
    return JsonResponse({"stock": variant.stock})
