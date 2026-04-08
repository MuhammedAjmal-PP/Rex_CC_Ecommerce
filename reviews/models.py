from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    """
    A product review tied to a specific user and product.
    One review per user per product (not per variant).
    Only users who have received a DELIVERED order item for
    the product are eligible to leave a review.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, "Rating must be at least 1."),
            MaxValueValidator(5, "Rating cannot exceed 5."),
        ],
    )

    title = models.CharField(
        max_length=120,
        help_text="A short summary of your review.",
    )

    comment = models.TextField(
        max_length=1000,
        help_text="Share your experience with this timepiece.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Soft-delete / moderation flag.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        # One review per user per product
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_review_per_user_product",
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.product.name} ({self.rating}★)"
