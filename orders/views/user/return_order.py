from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from orders.forms import ReturnForm
from orders.models import Order, OrderItem, ReturnImage
from orders.service.returns import (
    DuplicateReturnError,
    ReturnNotEligibleError,
    validate_return_eligibility,
)
from orders.service.status import InvalidTransitionError, change_order_item_status


@login_required
@require_GET
@never_cache
def return_order(request, order_number, item_id):
    """
    Render the return form for a single delivered order item.
    """
    order = get_object_or_404(Order, user=request.user, order_number=order_number)
    order_item = get_object_or_404(
        OrderItem.objects.select_related(
            "product_variant", "product_variant__product", "product_variant__product__brand"
        ),
        id=item_id,
        order=order,
    )

    try:
        validate_return_eligibility(order_item)
    except ReturnNotEligibleError:
        messages.error(request, "This item is not eligible for return.")
        return redirect(
            "user_order_details",
            order_number=order.order_number,
        )
    except DuplicateReturnError:
        messages.info(request, "A return request already exists for this item.")
        return redirect(
            "user_order_details",
            order_number=order.order_number,
        )

    form = ReturnForm()

    context = {
        "order": order,
        "order_item": order_item,
        "form": form,
        "primary_image": order_item.product_variant.primary_image,
    }
    return render(request, "orders/user/return_order.html", context)


@login_required
@require_POST
@never_cache
def return_order_submit(request, order_number, item_id):
    """
    Process the return form submission.
    """
    order = get_object_or_404(Order, user=request.user, order_number=order_number)
    order_item = get_object_or_404(
        OrderItem.objects.select_related("product_variant"),
        id=item_id,
        order=order,
    )

    try:
        validate_return_eligibility(order_item)
    except ReturnNotEligibleError:
        messages.error(request, "This item is not eligible for return.")
        return redirect(
            "user_order_details",
            order_number=order.order_number,
        )
    except DuplicateReturnError:
        messages.info(request, "A return request already exists for this item.")
        return redirect(
            "user_order_details",
            order_number=order.order_number,
        )

    form = ReturnForm(request.POST, request.FILES)

    if not form.is_valid():
        context = {
            "order": order,
            "order_item": order_item,
            "form": form,
            "primary_image": order_item.product_variant.primary_image,
        }
        return render(request, "orders/user/return_order.html", context)

    # Validate photos (count limit)
    photos = request.FILES.getlist("photos")
    if len(photos) > 3:
        context = {
            "order": order,
            "order_item": order_item,
            "form": form,
            "primary_image": order_item.product_variant.primary_image,
            "photo_errors": "You can upload a maximum of 3 photos.",
        }
        return render(request, "orders/user/return_order.html", context)

    # Create the Return record (L2 fix: wrap in atomic)
    try:
        with transaction.atomic():
            return_obj = form.save(commit=False)
            return_obj.order_item = order_item
            return_obj.save()

            # Save uploaded photos
            for photo in photos:
                ReturnImage.objects.create(return_request=return_obj, image=photo)

            # Transition item status: DELIVERED → RETURN_REQUESTED
            change_order_item_status(
                order_item=order_item,
                to_status="RETURN_REQUESTED",
                actor=request.user,
                note=f"Return requested by customer. Reason: {return_obj.reason_code}",
            )
    except InvalidTransitionError as error:
        messages.error(request, f"Unable to process return: {error}")
        return redirect(
            "user_order_details",
            order_number=order.order_number,
        )

    messages.success(
        request,
        "Return request submitted successfully. We'll review it shortly.",
    )
    return redirect(
        "user_order_details",
        order_number=order.order_number,
    )
