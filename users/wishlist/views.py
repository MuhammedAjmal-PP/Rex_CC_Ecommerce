from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from catalog.models import Product, ProductVariant
from users.cart.models import Cart, CartItem
from users.wishlist.models import Wishlist, WishlistItem
from users.wishlist.utils import (
    get_session_wishlist,
    toggle_session_wishlist,
)


@require_GET
def list_wishlist(request):
    # Get or create wishlist for the user
    if request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

        wishlist_items = (
            WishlistItem.objects.filter(
                wishlist=wishlist,
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
        items = [item.product_variant for item in wishlist_items]

    else:  # GUEST USER
        variant_ids = get_session_wishlist(request)
        items = (
            ProductVariant.objects.filter(
                id__in=variant_ids,
                is_deleted=False,
                is_drafted=False,
                product__is_deleted=False,
                product__is_drafted=False,
            )
            .select_related(
                "product",
                "product__brand",
            )
            .prefetch_related("images")
        )

    products = []

    for variant in items:
        image = variant.images.filter(is_primary=True).first()
        
        # Build variant details
        variant_details = []
        if variant.dial_color:
            variant_details.append(f"{variant.dial_color} Dial")
        if variant.case_size_mm:
            variant_details.append(f"{variant.case_size_mm}mm")
        if variant.strap_material:
            variant_details.append(variant.strap_material)
        if variant.movement_type:
            variant_details.append(variant.movement_type)

        products.append(
            {
                "variant": variant.id,
                "sku": variant.sku,
                "slug": variant.product.slug,
                "product_name": variant.product.name,
                "brand": variant.product.brand.name,
                "price": str(variant.price),
                "final_price": str(variant.final_price),
                "stock": variant.stock,
                "is_in_stock": variant.stock > 0,
                "image": image.image.url,
                "variant_details": variant_details,
            }
        )

    return JsonResponse({"success": True, "count": len(products), "products": products})



@require_POST
def wishlist_toggle(request, slug, sku):
    """Toggle wishlist item for user or guest (remove or add items into wishlist)"""
    product = get_object_or_404(Product, slug=slug, is_drafted=False, is_deleted=False)
    variant = get_object_or_404(
        ProductVariant, product=product, sku=sku, is_drafted=False, is_deleted=False
    )

    # AUTHENTICATED USER
    if request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

        wishlist_item = WishlistItem.objects.filter(
            wishlist=wishlist,
            product_variant=variant,
        ).first()

        if wishlist_item:
            wishlist_item.delete()
            message = "Removed from your wishlist"
            added = False
        else:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_item = CartItem.objects.filter(
                cart=cart, product_variant=variant
            ).first()
            if cart_item:
                message = "This item is already in your cart"
                added = False
            else:
                WishlistItem.objects.create(
                    wishlist=wishlist,
                    product_variant=variant,
                )
                message = "Added to wishlist ❤️"
                added = True

        return JsonResponse(
            {
                "success": True,
                "message": message,
                "added": added,
            }
        )

    # GUEST USER
    message, added = toggle_session_wishlist(request, variant.id)

    return JsonResponse(
        {
            "success": True,
            "message": message,
            "added": added,
            "guest": True,
        }
    )


@never_cache
@login_required
def view_wishlist(request):
    return render(request, "wishlist/wishlist.html")
