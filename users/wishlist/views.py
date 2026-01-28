from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from catalog.models import ProductVariant
from users.wishlist.models import Wishlist, WishlistItem
from users.wishlist.utils import (
    add_to_session_wishlist,
    get_session_wishlist,
    remove_from_session_wishlist,
)


@require_GET
def view_wishlist(request):
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
def add_wishlist(request, variant_id):
    """Add items into wishlist"""
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist, product_variant=variant
        )

        if created:
            message = "Added to wishlist ❤️"
        else:
            message = "Already in your wishlist"

        return JsonResponse(
            {
                "success": True,
                "message": message,
            }
        )
    # GUEST USER → SESSION
    message = add_to_session_wishlist(request, variant.id)

    return JsonResponse(
        {
            "success": True,
            "message": message,
            "guest": True,
        }
    )


@require_POST
def remove_wishlist(request, variant_id):
    """Remove items from wishlist"""
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.user.is_authenticated:
        wishlist = get_object_or_404(Wishlist, user=request.user)
        WishlistItem.objects.filter(wishlist=wishlist, product_variant=variant).delete()
        return JsonResponse({"success": True})

    remove_from_session_wishlist(request, variant.id)
    return JsonResponse({"success": True})
