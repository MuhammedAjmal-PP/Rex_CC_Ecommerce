from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from catalog.models import Product
from orders.models import OrderItem
from reviews.forms import ReviewForm
from reviews.models import Review


@login_required
@require_POST
def submit_review(request, product_id):
    """
    AJAX endpoint — submit a new review for a product.
    Returns JSON with success/errors.
    """
    product = get_object_or_404(Product, id=product_id)

    # Check 1: user has a delivered item for this product
    has_delivered = OrderItem.objects.filter(
        order__user=request.user,
        product_variant__product_id=product.pk,
        status="DELIVERED",
    ).exists()

    # Fallback: check order-level delivery status
    if not has_delivered:
        has_delivered = OrderItem.objects.filter(
            order__user=request.user,
            order__status="DELIVERED",
            product_variant__product_id=product.pk,
        ).exists()

    if not has_delivered:
        return JsonResponse(
            {"success": False, "message": "You need a delivered order to review this product."},
            status=403,
        )

    # Check 2: not already reviewed
    already_reviewed = Review.objects.filter(
        user=request.user, product_id=product.pk
    ).exists()

    if already_reviewed:
        return JsonResponse(
            {"success": False, "message": "You have already reviewed this product."},
            status=403,
        )

    form = ReviewForm(request.POST)

    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        try:
            review.save()
            review.refresh_from_db()
        except Exception:
            return JsonResponse(
                {"success": False, "message": "Could not save review. Please try again."},
                status=400,
            )

        from django.utils import timezone

        date_str = (
            review.created_at.strftime("%B %d, %Y")
            if review.created_at
            else timezone.now().strftime("%B %d, %Y")
        )

        return JsonResponse({
            "success": True,
            "review": {
                "author": request.user.get_full_name or request.user.email,
                "date": date_str,
                "rating": review.rating,
                "title": review.title,
                "comment": review.comment,
            },
        })

    # Return per-field errors
    errors = {field: errs[0] for field, errs in form.errors.items()}
    return JsonResponse({"success": False, "errors": errors}, status=400)

