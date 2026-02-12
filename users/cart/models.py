from decimal import Decimal
from django.conf import settings
from django.db import models

# Create your models here.


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

    @property
    def sub_total(self):
        return sum(item.total_amount for item in self.items.all())

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def shipping_fee(self):
        return Decimal("100.00") * self.total_quantity

    @property
    def total_amount(self):
        return self.sub_total + self.shipping_fee

    @property
    def tax(self):
        return self.total_amount * Decimal(settings.GST_RATE) / Decimal(100)

    @property
    def grand_total(self):
        return self.total_amount + self.tax

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

    @property
    def total_amount(self):
        return self.product_variant.final_price * self.quantity

    @property
    def total_discount(self):
        return self.product_variant.discount_amount * self.quantity

    def __str__(self):
        return f"{self.product_variant} added at {self.added_at}"
