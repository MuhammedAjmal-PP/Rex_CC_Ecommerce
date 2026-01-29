from django.urls import path
from users.wishlist.views import list_wishlist, view_wishlist, wishlist_toggle

urlpatterns = [
    path("api/wishlist/", list_wishlist, name="wishlist_list"),
    path(
        "api/wishlist/<int:variant_id>/toggle/",
        wishlist_toggle,
        name="wishlist_toggle",
    ),
    path("profile/wishlist/", view_wishlist, name="user_wishlist"),
]
