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
    def _summary(self):
        """Compute all cart metrics in a SINGLE pass over items."""
        if hasattr(self, "_cached_summary"):
            return self._cached_summary

        sub_total = Decimal("0.00")
        total = Decimal("0.00")
        discount = Decimal("0.00")
        shipping_fee = Decimal("0.00")

        for item in self.items.all():
            sub_total += item.total_amount
            total += item.total_base
            discount += item.total_discount
            shipping_fee += Decimal(item.quantity * settings.SHIPPING_CHARGE)

        total_amount = sub_total + shipping_fee
        tax = total_amount * Decimal(settings.GST_RATE) / Decimal(100)
        grand_total = total_amount + tax

        self._cached_summary = {
            "sub_total": sub_total,
            "total": total,
            "discount": discount,
            "shipping_fee": shipping_fee,
            "total_amount": total_amount,
            "tax": tax,
            "grand_total": grand_total,
        }
        return self._cached_summary

    @property
    def sub_total(self):
        return self._summary["sub_total"]

    @property
    def total(self):
        return self._summary["total"]

    @property
    def discount(self):
        return self._summary["discount"]

    @property
    def shipping_fee(self):
        return self._summary["shipping_fee"]

    @property
    def total_amount(self):
        return self._summary["total_amount"]

    @property
    def tax(self):
        return self._summary["tax"]

    @property
    def grand_total(self):
        return self._summary["grand_total"]

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
    def total_base(self):
        return self.product_variant.price * self.quantity

    @property
    def item_price(self):
        return self.product_variant.final_price

    @property
    def total_discount(self):
        return self.product_variant.discount_amount * self.quantity

    def __str__(self):
        return f"{self.product_variant} added at {self.added_at}"
