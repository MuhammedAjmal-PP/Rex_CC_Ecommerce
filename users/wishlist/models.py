from django.db import models

# Create your models here.


class Wishlist(models.Model):
    user = models.OneToOneField(
        "accounts.CustomUser", on_delete=models.CASCADE, related_name="wishlist"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}'s Wishlist"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    product_variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("wishlist", "product_variant")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.product_variant} added at {self.added_at}"
