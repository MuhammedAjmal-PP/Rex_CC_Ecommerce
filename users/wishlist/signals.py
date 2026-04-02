from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from users.cart.models import Cart
from users.wishlist.models import Wishlist, WishlistItem


@receiver(user_logged_in)
def merge_session_wishlist(sender, request, user, **kwargs):
    session_wishlist = request.session.get("wishlist")

    if not session_wishlist:
        return

    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    cart, _ = Cart.objects.get_or_create(user=user)

    user_wishlist = set(wishlist.items.values_list("product_variant_id", flat=True))
    user_cart = set(cart.items.values_list("product_variant", flat=True))

    for variant_id in session_wishlist:
        if variant_id not in user_wishlist and variant_id not in user_cart:
            WishlistItem.objects.create(
                wishlist=wishlist,
                product_variant_id=variant_id,
            )

    # Clear session wishlist
    request.session.pop("wishlist", None)
    request.session.modified = True
