from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from catalog.models import ProductVariant
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

        products.append(
            {
                "variant": variant.id,
                "sku": variant.sku,
                "product_name": variant.product.name,
                "brand": variant.product.brand.name,
                "price": str(variant.price),
                "final_price": str(variant.final_price),
                "stock": variant.stock,
                "is_in_stock": variant.stock > 0,
                "image": image.image.url,
            }
        )

    return JsonResponse({"success": True, "count": len(products), "products": products})


@require_POST
def wishlist_toggle(request, variant_id):
    """Toggle wishlist item for user or guest (remove or add items into wishlist)"""
    variant = get_object_or_404(ProductVariant, id=variant_id)

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
