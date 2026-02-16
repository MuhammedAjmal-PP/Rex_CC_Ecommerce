from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from orders.models import Order, OrderItem
from orders.service import (
    InvalidTransitionError,
    change_order_item_status,
    change_order_status,
)
from orders.service.status import (
    ORDER_ALLOWED_TRANSITIONS,
    ORDER_ITEM_ALLOWED_TRANSITIONS,
)


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
def order_list(request):
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all").strip().upper()

    orders_qs = (
        Order.objects.select_related("user")
        .prefetch_related("status")
        .order_by("-created_at")
    )

    if search_query:
        orders_qs = orders_qs.filter(
            Q(order_number__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
        )

    orders_list = list(orders_qs)

    if status_filter != "ALL":
        orders_list = [
            order
            for order in orders_list
            if order.current_status and order.current_status.status == status_filter
        ]

    total_orders = len(orders_list)
    confirmed_orders = sum(
        1
        for order in orders_list
        if order.current_status and order.current_status.status == "CONFIRMED"
    )
    shipped_orders = sum(
        1
        for order in orders_list
        if order.current_status and order.current_status.status == "SHIPPED"
    )
    delivered_orders = sum(
        1
        for order in orders_list
        if order.current_status and order.current_status.status == "DELIVERED"
    )
    cancelled_orders = sum(
        1
        for order in orders_list
        if order.current_status and order.current_status.status == "CANCELLED"
    )

    paginator = Paginator(orders_list, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "orders": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "total_orders": total_orders,
        "confirmed_orders": confirmed_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
    }
    return render(request, "orders/admin/order_list.html", context)


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
@require_GET
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("status"),
        order_number=order_number,
    )
    order_items = (
        OrderItem.objects.filter(order=order)
        .select_related(
            "product_variant",
            "product_variant__product",
            "product_variant__product__brand",
        )
        .prefetch_related("product_variant__images", "status")
    )

    order_current = order.current_status.status if order.current_status else None
    order_next = sorted(ORDER_ALLOWED_TRANSITIONS.get(order_current, set()))

    items_with_transitions = []
    for item in order_items:
        item_current = item.current_status.status if item.current_status else None
        item_next = sorted(
            ORDER_ITEM_ALLOWED_TRANSITIONS.get(item_current, set())
        )
        # Per-item timeline: oldest → newest for horizontal display
        item_timeline = list(
            item.status.select_related("actor").order_by("created_at")
        )
        items_with_transitions.append(
            {
                "item": item,
                "current_status": item_current,
                "allowed_next": item_next,
                "timeline": item_timeline,
            }
        )

    # Order-only timeline: oldest → newest
    order_only_timeline = list(
        order.status.select_related("actor").order_by("created_at")
    )

    context = {
        "order": order,
        "order_current": order_current,
        "order_next": order_next,
        "items_with_transitions": items_with_transitions,
        "order_only_timeline": order_only_timeline,
    }

    return render(request, "orders/admin/order_details.html", context)


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
@require_POST
def order_status_update(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    to_status = request.POST.get("to_status", "").strip().upper()

    if not to_status:
        messages.error(request, "Please choose a valid order status.")
        return redirect(request.META.get("HTTP_REFERER", reverse("admin_orders_list")))

    try:
        change_order_status(
            order=order,
            to_status=to_status,
            actor=request.user,
            note=f"Order status updated by admin to {to_status}",
        )
        messages.success(request, f"Order status changed to {to_status}.")
    except InvalidTransitionError as error:
        messages.error(request, f"Invalid order transition: {error}")

    return redirect(request.META.get("HTTP_REFERER", reverse("admin_orders_list")))


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
@require_POST
def order_item_status_update(request, order_number, item_id):
    order = get_object_or_404(Order, order_number=order_number)
    order_item = get_object_or_404(OrderItem, order=order, id=item_id)
    to_status = request.POST.get("to_status", "").strip().upper()

    if not to_status:
        messages.error(request, "Please choose a valid item status.")
        return redirect(request.META.get("HTTP_REFERER", reverse("admin_orders_list")))

    try:
        change_order_item_status(
            order_item=order_item,
            to_status=to_status,
            actor=request.user,
            note=f"Order item status updated by admin to {to_status}",
        )
        messages.success(
            request, f"Item #{order_item.id} status changed to {to_status}."
        )
    except InvalidTransitionError as error:
        messages.error(request, f"Invalid item transition: {error}")

    return redirect(request.META.get("HTTP_REFERER", reverse("admin_orders_list")))
