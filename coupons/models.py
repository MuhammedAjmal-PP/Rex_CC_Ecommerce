from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.utils import timezone


# ======================================================
# COUPON MODEL
# ======================================================


class ActiveCouponManager(models.Manager):
    """Returns only non-deleted coupons."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Coupon(models.Model):

    DISCOUNT_TYPE_CHOICES = (
        ("PERCENTAGE", "Percentage"),
        ("FIXED", "Fixed Amount"),
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        validators=[MinLengthValidator(3)],
        help_text="Unique coupon code (auto-uppercased on save)",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Admin-facing description of the coupon",
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default="PERCENTAGE",
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Percentage (e.g. 10 for 10%) or fixed amount (e.g. 500)",
    )

    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Minimum cart subtotal required to use this coupon",
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cap on discount for percentage coupons (leave blank for no cap)",
    )

    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total uses allowed across all users (blank = unlimited)",
    )
    per_user_limit = models.PositiveIntegerField(
        default=1,
        help_text="Max uses per individual user",
    )
    used_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Current total usage counter",
    )

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()          # default — includes deleted
    active = ActiveCouponManager()      # excludes soft-deleted

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    # ─────────────────────────────────────────────
    # Validity check
    # ─────────────────────────────────────────────

    @property
    def is_valid(self):
        """Check if coupon is active, within date range, and not exhausted."""
        now = timezone.now()
        if not self.is_active:
            return False
        if not (self.start_date <= now <= self.end_date):
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        return True

    @property
    def is_expired(self):
        return timezone.now() > self.end_date

    # ─────────────────────────────────────────────
    # Discount calculation
    # ─────────────────────────────────────────────

    def calculate_discount(self, subtotal):
        """
        Return the actual discount amount for a given subtotal.
        Respects max_discount_amount cap for percentage coupons.
        """
        subtotal = Decimal(str(subtotal))

        if self.discount_type == "PERCENTAGE":
            raw = subtotal * self.discount_value / Decimal("100")
            if self.max_discount_amount:
                raw = min(raw, self.max_discount_amount)
        else:
            # FIXED
            raw = min(self.discount_value, subtotal)

        return raw.quantize(Decimal("0.01"))

    # ─────────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────────

    def _date_changed(self, field_name):
        if not self.pk:
            return True
        saved = (
            Coupon.objects.filter(pk=self.pk)
            .values_list(field_name, flat=True)
            .first()
        )
        return saved != getattr(self, field_name)

    def clean(self):
        errors = {}
        now = timezone.now()

        if self.start_date and self._date_changed("start_date"):
            if self.start_date < now:
                errors["start_date"] = "Start date cannot be in the past."

        if self.end_date and self._date_changed("end_date"):
            if self.end_date <= now:
                errors["end_date"] = "End date must be in the future."

        if self.start_date and self.end_date and self.start_date >= self.end_date:
            errors.setdefault("end_date", "End date must be after start date.")

        if self.discount_value is not None and self.discount_value <= 0:
            errors["discount_value"] = "Discount value must be greater than 0."

        if (
            self.discount_type == "PERCENTAGE"
            and self.discount_value is not None
            and self.discount_value > 100
        ):
            errors["discount_value"] = "Percentage discount cannot exceed 100%."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        """Mark this coupon as deleted instead of removing from DB."""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active", "updated_at"])


# ======================================================
# COUPON USAGE MODEL
# ======================================================


class CouponUsage(models.Model):
    """Tracks each use of a coupon by a user, linked to an order."""

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.PROTECT,
        related_name="usages",
    )
    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="coupon_usages",
    )
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_usage",
    )
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-used_at"]

    def __str__(self):
        return f"{self.user} used {self.coupon.code} on {self.used_at:%Y-%m-%d}"
