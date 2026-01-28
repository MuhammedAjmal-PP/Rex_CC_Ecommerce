from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from users.wishlist.models import Wishlist, WishlistItem


@login_required
@require_GET
def view_wishlist(request):
    # Get or create wishlist for the user
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
    print(wishlist_items)

    products = []

    for item in wishlist_items:
        variant = item.product_variant
        product = variant.product
        brand = product.brand
        image = variant.images.filter(is_primary=True).first()

        products.append(
            {
                "item_id": item.id,
                "added_at": item.added_at.isoformat(),
                "variant": variant.id,
                "sku": variant.sku,
                "product_name": product.name,
                "brand": brand.name if brand else "",
                "price": str(variant.price),
                "final_price": str(variant.final_price),
                "stock": variant.stock,
                "is_in_stock": variant.stock > 0,
                "image": image.image.url,
            }
        )

    return JsonResponse({"success": True, "count": len(products), "products": products})
