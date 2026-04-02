from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.cache import never_cache
from orders.models import Order, OrderItem
from orders.utils import (
    can_generate_invoice,
    can_return_item,
    compute_item_totals,
    compute_return_refund,
    get_payment_transaction,
)
from weasyprint import HTML


@login_required
@never_cache
def order_list(request):
    """Order listing view with search, date filtering, and pagination."""
    search = request.GET.get("q", "").strip()
    date_filter = request.GET.get("date_filter", "").strip().lower()

    orders = (
        Order.objects.filter(user=request.user)
        .exclude(status__in=("EXPIRED", "STOCK_UNAVAILABLE"))
        .prefetch_related("payment")
    )

    if search:
        orders = orders.filter(
            Q(order_number__iexact=search)
            | Q(items__product_variant__sku__icontains=search)
            | Q(items__product_variant__product__name__icontains=search)
        ).distinct()

    now = timezone.now()
    if date_filter == "today":
        orders = orders.filter(created_at__date=now.date())
    elif date_filter == "7d":
        orders = orders.filter(created_at__gte=now - timedelta(days=7))
    elif date_filter == "30d":
        orders = orders.filter(created_at__gte=now - timedelta(days=30))
    elif date_filter == "last_year":
        orders = orders.filter(created_at__gte=now - timedelta(days=365))

    page_obj = Paginator(orders.order_by("-created_at"), 10).get_page(
        request.GET.get("page")
    )

    # Build set of order IDs eligible for Razorpay retry; attach payment_txn to each order
    razorpay_retry_ids = set()
    for order in page_obj:
        payment = get_payment_transaction(order)
        order.payment_txn = payment
        if order.status == "FAILED" and order.cart_snapshot:
            if payment and payment.payment_method == "RAZORPAY":
                razorpay_retry_ids.add(order.pk)

    context = {
        "orders": page_obj,
        "q": search,
        "date_filter": date_filter,
        "page_obj": page_obj,
        "razorpay_retry_ids": razorpay_retry_ids,
    }
    return render(request, "orders/user/order_list.html", context)


@never_cache
@login_required
def order_detail(request, order_number):
    """Order details page with order-level and item-level status data."""
    order = get_object_or_404(
        Order.objects.prefetch_related("payment"),
        user=request.user,
        order_number=order_number,
    )

    # Block details page for failed/expired/stock-unavailable orders
    if order.status in ("FAILED", "EXPIRED", "STOCK_UNAVAILABLE"):
        messages.error(request, "This order cannot be viewed.")
        return redirect("user_order_list")

    order_items = (
        OrderItem.objects.filter(order=order)
        .select_related(
            "product_variant",
            "product_variant__product",
            "product_variant__product__brand",
            "return_request",
        )
        .prefetch_related("product_variant__images", "transactions")
    )

    is_cancellable = order.status in ("PLACED", "CONFIRMED")

    # ── Stepper data for the horizontal tracker ──
    stepper_steps = [
        ("PLACED", "Order Placed", "shopping_cart"),
        ("CONFIRMED", "Confirmed", "inventory"),
        ("SHIPPED", "Shipped", "local_shipping"),
        ("OUT_FOR_DELIVERY", "Out for Delivery", "delivery_dining"),
        ("DELIVERED", "Delivered", "home"),
    ]
    status_order = [s[0] for s in stepper_steps]
    current_idx = (
        status_order.index(order.status) if order.status in status_order else -1
    )
    completed_steps = set(status_order[:current_idx]) if current_idx > 0 else set()

    # Enrich items with computed values for template
    items_list = list(order_items)
    for item in items_list:
        totals = compute_item_totals(item)
        item.total_original_price = totals["total_original_price"]
        item.item_discount = totals["item_discount"]
        item.can_return = can_return_item(item)
        item.total_return = compute_return_refund(item)

    payment = get_payment_transaction(order)

    context = {
        "order": order,
        "items": items_list,
        "gst_rate": settings.GST_RATE,
        "is_cancellable": is_cancellable,
        "stepper_steps": stepper_steps,
        "completed_steps": completed_steps,
        "payment": payment,
        "can_invoice": can_generate_invoice(order),
    }
    return render(request, "orders/user/order_detail.html", context)


@login_required
@never_cache
def order_invoice(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related("payment"),
        user=request.user,
        order_number=order_number,
    )
    order_items = (
        OrderItem.objects.filter(order=order)
        .select_related(
            "product_variant",
            "product_variant__product",
            "product_variant__product__brand",
        )
        .prefetch_related("product_variant__images")
    )

    if not can_generate_invoice(order):
        messages.warning(request, "Invoice will be available after order confirmation.")
        return redirect("user_order_details", order_number=order.order_number)

    html_string = render_to_string(
        "orders/user/order_invoice.html",
        {
            "order": order,
            "order_items": order_items,
            "payment": get_payment_transaction(order),
            "gst_rate": settings.GST_RATE,
            "hsn_code": settings.DEFAULT_WATCH_HSN,
            "store_state": settings.STORE_STATE,
            "store_state_code": settings.STORE_STATE_CODE,
        },
    )

    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="invoice_{order.order_number}.pdf"'
    )
    return response
