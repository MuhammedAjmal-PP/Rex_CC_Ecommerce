from django.urls import path
from users.wishlist.views import add_wishlist, remove_wishlist, view_wishlist

urlpatterns = [
    path("api/wishlist/", view_wishlist, name="user_wishlist"),
    path("api/wishlist/<int:variant_id>/add/", add_wishlist, name="add_wishlist"),
    path(
        "api/wishlist/<int:variant_id>/remove/",
        remove_wishlist,
        name="remove_wishlist",
    ),
]
