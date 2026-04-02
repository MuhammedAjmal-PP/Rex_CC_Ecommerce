from django.db import models


class Cart(models.Model):

    user = models.OneToOneField(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def items_count(self):
        return self.items.count()

    def __str__(self):
        return f"{self.user}'s cart"


class CartItem(models.Model):

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product_variant")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.product_variant} added at {self.added_at}"
