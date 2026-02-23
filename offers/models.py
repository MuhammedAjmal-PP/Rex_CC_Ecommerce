from decimal import Decimal
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.utils import timezone


class Offer(models.Model):

    OFFER_TYPE_CHOICES = (
        ("PRODUCT", "Product Offer"),
        ("CATEGORY", "Category Offer"),
        ("BRAND", "Brand Offer"),
    )

    DISCOUNT_TYPE_CHOICES = (
        ("PERCENTAGE", "Percentage"),
        # ("FIXED", "Fixed Amount"), # Uncomment for future expansion
    )

    name = models.CharField(max_length=100, validators=[MinLengthValidator(3)])

    offer_type = models.CharField(
        max_length=20,
        choices=OFFER_TYPE_CHOICES,
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default="PERCENTAGE",
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text="Percentage value (e.g., 10 for 10%)",
    )

    is_active = models.BooleanField(default=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # ─────────────────────────────────────────────
    # Relations (Attach offer to target)
    # ─────────────────────────────────────────────
    products = models.ManyToManyField(
        "catalog.Product",
        blank=True,
        related_name="offers",
    )

    categories = models.ManyToManyField(
        "catalog.Category",
        blank=True,
        related_name="offers",
    )

    brands = models.ManyToManyField(
        "catalog.Brand",
        blank=True,
        related_name="offers",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.offer_type})"

    @property
    def is_valid(self):
        """
        Check if offer is active and within date range.
        """
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
