from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
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
    ADMIN_ITEM_ALLOWED_TRANSITIONS,
    ADMIN_ORDER_ALLOWED_TRANSITIONS,
)
from orders.utils import compute_item_totals, get_payment_transaction


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
def order_list(request):
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all").strip().upper()

    orders_qs = (
        Order.objects.select_related("user")
        .prefetch_related("payment")
        .order_by("-created_at")
    )

    if search_query:
        orders_qs = orders_qs.filter(
            Q(order_number__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
        )

    # DB-level status counts (computed on the searched but unfiltered queryset)
    status_agg = orders_qs.aggregate(
        total=Count("id"),
        confirmed=Count("id", filter=Q(status="CONFIRMED")),
        shipped=Count("id", filter=Q(status="SHIPPED")),
        delivered=Count("id", filter=Q(status="DELIVERED")),
        cancelled=Count(
            "id",
            filter=Q(status__in=("CANCELLED", "EXPIRED", "STOCK_UNAVAILABLE")),
        ),
    )

    # DB-level status filter
    if status_filter == "CANCELLED":
        # Group EXPIRED and STOCK_UNAVAILABLE under "Cancelled" tab
        orders_qs = orders_qs.filter(
            status__in=("CANCELLED", "EXPIRED", "STOCK_UNAVAILABLE")
        )
    elif status_filter != "ALL":
        orders_qs = orders_qs.filter(status=status_filter)

    paginator = Paginator(orders_qs, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    # Attach _payment to each order for template access
    for order in page_obj:
        order.payment_txn = get_payment_transaction(order)

    context = {
        "orders": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "total_orders": status_agg["total"],
        "confirmed_orders": status_agg["confirmed"],
        "shipped_orders": status_agg["shipped"],
        "delivered_orders": status_agg["delivered"],
        "cancelled_orders": status_agg["cancelled"],
    }
    return render(request, "orders/admin/order_list.html", context)


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
@require_GET
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("payment"),
        order_number=order_number,
    )

    # Block details page for failed/expired/stock-unavailable orders
    if order.status in ("FAILED", "EXPIRED", "STOCK_UNAVAILABLE"):
        messages.error(request, "This order cannot be managed.")
        return redirect("admin_orders_list")
    order_items = (
        OrderItem.objects.filter(order=order)
        .select_related(
            "product_variant",
            "product_variant__product",
            "product_variant__product__brand",
        )
        .prefetch_related("product_variant__images")
    )

    order_current = order.status
    order_next = sorted(ADMIN_ORDER_ALLOWED_TRANSITIONS.get(order_current, set()))

    items_with_transitions = []
    for item in order_items:
        item_current = item.status
        item_next = sorted(ADMIN_ITEM_ALLOWED_TRANSITIONS.get(item_current, set()))
        totals = compute_item_totals(item)
        items_with_transitions.append(
            {
                "item": item,
                "current_status": item_current,
                "allowed_next": item_next,
                "total_original_price": totals["total_original_price"],
            }
        )

    context = {
        "order": order,
        "order_current": order_current,
        "order_next": order_next,
        "items_with_transitions": items_with_transitions,
        "gst_rate": settings.GST_RATE,
        "payment": get_payment_transaction(order),
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
        change_order_status(order=order, to_status=to_status)
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
        change_order_item_status(order_item=order_item, to_status=to_status)
        messages.success(
            request, f"Item #{order_item.id} status changed to {to_status}."
        )
    except InvalidTransitionError as error:
        messages.error(request, f"Invalid item transition: {error}")

    return redirect(request.META.get("HTTP_REFERER", reverse("admin_orders_list")))
