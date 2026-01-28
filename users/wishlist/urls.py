from django.urls import path
from users.wishlist.views import view_wishlist

urlpatterns = [
    path("api/wishlist/", view_wishlist, name="user_wishlist"),
]
