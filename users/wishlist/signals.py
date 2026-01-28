from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from users.wishlist.models import Wishlist, WishlistItem
from catalog.models import ProductVariant


@receiver(user_logged_in)
def merge_session_wishlist(sender, request, user, **kwargs):
    session_wishlist = request.session.get("wishlist")

    if not session_wishlist:
        return

    wishlist, _ = Wishlist.objects.get_or_create(user=user)

    existing_variants = set(wishlist.items.values_list("product_variant_id", flat=True))

    for variant_id in session_wishlist:
        if variant_id not in existing_variants:
            WishlistItem.objects.create(
                wishlist=wishlist,
                product_variant_id=variant_id,
            )

    # Clear session wishlist
    request.session.pop("wishlist", None)
    request.session.modified = True
