from django.core.exceptions import ValidationError
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

    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(3)],
    )

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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.offer_type})"

    # ─────────────────────────────────────────────
    
    def _date_changed(self, field_name):
        """Return True if the field was changed from its saved DB value (or is new)."""
        if not self.pk:
            return True
        saved = Offer.objects.filter(pk=self.pk).values_list(field_name, flat=True).first()
        return saved != getattr(self, field_name)

    def clean(self):
        errors = {}
        now = timezone.now()

        # Only enforced when the date is new or actually changed
        if self.start_date and self._date_changed("start_date"):
            if self.start_date < now:
                errors["start_date"] = "Start date cannot be in the past."

        if self.end_date and self._date_changed("end_date"):
            if self.end_date <= now:
                errors["end_date"] = "End date must be in the future."

        # Date ordering 
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            errors.setdefault("end_date", "End date must be after start date.")

        # No zero-percent discounts 
        if self.discount_value is not None and self.discount_value <= 0:
            errors["discount_value"] = "Discount value must be greater than 0."

        # Percentage cap 
        if (
            self.discount_type == "PERCENTAGE"
            and self.discount_value is not None
            and self.discount_value > 100
        ):
            errors["discount_value"] = "Percentage discount cannot exceed 100%."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Normalize name
        if self.name:
            self.name = self.name.strip()
        self.full_clean()
        super().save(*args, **kwargs)
