from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from orders.models import Order, OrderItem
from orders.service import InvalidTransitionError, change_order_item_status


CANCELLABLE_ITEM_STATUSES = {"PENDING", "CONFIRMED", "PACKING", "READY"}


@login_required
@require_GET
@never_cache
def cancel_order(request, order_number):
    order = get_object_or_404(Order, user=request.user, order_number=order_number)
    order_items = OrderItem.objects.filter(order=order).select_related(
        "product_variant", "product_variant__product"
    )

    cancellable_items = [
        item
        for item in order_items
        if item.current_status.status in CANCELLABLE_ITEM_STATUSES
    ]

    context = {
        "order": order,
        "order_items": order_items,
        "cancellable_items": cancellable_items,
        "cancellable_item_ids": {item.id for item in cancellable_items},
        "has_cancellable_items": bool(cancellable_items),
    }
    return render(request, "orders/user/cancel_order.html", context)


@login_required
@require_POST
@never_cache
def cancel_order_submit(request, order_number):
    order = get_object_or_404(Order, user=request.user, order_number=order_number)

    selected_ids = request.POST.getlist("item_ids")
    reason_note = request.POST.get("reason_note", "").strip()

    if not selected_ids:
        messages.error(request, "Please select at least one item to cancel.")
        return redirect("user_cancel_order", order_number=order.order_number)

    selected_items = list(
        OrderItem.objects.filter(order=order, id__in=selected_ids).select_related(
            "product_variant", "product_variant__product"
        )
    )

    if len(selected_items) != len(set(selected_ids)):
        messages.error(request, "Invalid item selection. Please try again.")
        return redirect("user_cancel_order", order_number=order.order_number)

    note = "Cancelled by user"
    if reason_note:
        note = f"Cancelled by user. Reason: {reason_note}"

    try:
        with transaction.atomic():
            cancelled_count = 0
            for item in selected_items:
                if not item.current_status:
                    raise InvalidTransitionError(
                        f"Item #{item.id} has no status and cannot be cancelled."
                    )

                change_order_item_status(
                    order_item=item,
                    to_status="CANCELLED",
                    actor=request.user,
                    note=note,
                )
                cancelled_count += 1
    except InvalidTransitionError as error:
        messages.error(request, f"Unable to cancel selected item(s): {error}")
        return redirect("user_cancel_order", order_number=order.order_number)

    messages.success(
        request,
        f"{cancelled_count} item(s) cancelled. Refund processing status will be visible in your wallet.",
    )
    return redirect("user_order_details", order_number=order.order_number)
