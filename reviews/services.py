"""
Reviews — Business Logic Layer
Keeps views thin by centralising review queries and eligibility checks.
"""

from django.db.models import Avg, Count, Q

from orders.models import OrderItem
from reviews.models import Review


def get_product_reviews(product, *, limit=None):
    """Return active reviews for a product, newest first."""
    qs = (
        Review.objects.filter(product=product, is_active=True)
        .select_related("user")
        .order_by("-created_at")
    )
    if limit:
        qs = qs[:limit]
    return qs


def get_ratings_summary(product):
    """
    Return a dict with average rating, total count, and
    per-star distribution (percentages).
    """
    reviews = Review.objects.filter(product=product, is_active=True)
    agg = reviews.aggregate(avg=Avg("rating"), total=Count("id"))

    average = round(agg["avg"] or 0, 1)
    total = agg["total"]

    # Per-star distribution (as percentages)
    distribution = {}
    if total > 0:
        star_counts = (
            reviews.values("rating")
            .annotate(cnt=Count("id"))
            .order_by("rating")
        )
        star_map = {row["rating"]: row["cnt"] for row in star_counts}
        for star in range(5, 0, -1):
            count = star_map.get(star, 0)
            distribution[star] = round(count / total * 100)
    else:
        for star in range(5, 0, -1):
            distribution[star] = 0

    return {
        "average": average,
        "total_reviews": total,
        "distribution": distribution,
    }


def can_review(user, product):
    """
    A user can review a product only if:
      1. They have at least one DELIVERED order item for any variant of the product.
      2. They have NOT already submitted an active review for this product.
    """
    if not user or not user.is_authenticated:
        return False

    has_delivered = OrderItem.objects.filter(
        order__user=user,
        product_variant__product_id=product.pk,
        status="DELIVERED",
    ).exists()

    if not has_delivered:
        # Fallback: also check if the entire ORDER is delivered
        from orders.models import Order

        has_delivered = OrderItem.objects.filter(
            order__user=user,
            order__status="DELIVERED",
            product_variant__product_id=product.pk,
        ).exists()

    if not has_delivered:
        return False

    already_reviewed = Review.objects.filter(
        user=user, product_id=product.pk
    ).exists()

    return not already_reviewed


def get_user_review(user, product):
    """Return the user's existing review for a product, or None."""
    if not user or not user.is_authenticated:
        return None
    return Review.objects.filter(user=user, product=product).first()
