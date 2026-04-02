from catalog.models import ProductVariant
from users.wishlist.models import WishlistItem


def get_session_wishlist(request):
    return request.session.get("wishlist", [])


def toggle_session_wishlist(request, variant_id):
    wishlist = request.session.get("wishlist", [])

    if variant_id in wishlist:
        wishlist.remove(variant_id)
        message = "Removed from your wishlist"
        added = False
    else:
        wishlist.append(variant_id)
        message = "Added to wishlist ❤️"
        added = True

    request.session["wishlist"] = wishlist
    request.session.modified = True

    return message, added


def get_wishlist_variant_ids(request):
    if request.user.is_authenticated:
        return list(
            WishlistItem.objects.filter(
                wishlist__user=request.user,
                product_variant__is_deleted=False,
                product_variant__is_drafted=False,
                product_variant__product__is_deleted=False,
                product_variant__product__is_drafted=False,
            ).values_list("product_variant_id", flat=True)
        )

    # Guest wishlist cleanup
    session_ids = request.session.get("wishlist", [])
    valid_ids = list(
        ProductVariant.objects.filter(
            id__in=session_ids,
            is_deleted=False,
            is_drafted=False,
            product__is_deleted=False,
            product__is_drafted=False,
        ).values_list("id", flat=True)
    )

    # Update session (self-healing)
    request.session["wishlist"] = valid_ids
    request.session.modified = True

    return valid_ids
