from django.apps import AppConfig


class WishlistConfig(AppConfig):
    name = "users.wishlist"

    def ready(self):
        import users.wishlist.signals
