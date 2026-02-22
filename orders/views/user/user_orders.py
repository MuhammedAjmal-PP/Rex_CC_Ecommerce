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
from weasyprint import HTML


@login_required
@never_cache
def order_list(request):
    """Order listing view with search, date filtering, and pagination."""
    search = request.GET.get("q", "").strip()
    date_filter = request.GET.get("date_filter", "").strip().lower()

    orders = Order.objects.filter(user=request.user).prefetch_related(
        "status", "payment"
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
    context = {
        "orders": page_obj,
        "q": search,
        "date_filter": date_filter,
        "page_obj": page_obj,
    }
    return render(request, "orders/user/order_list.html", context)


@never_cache
@login_required
def order_detail(request, order_number):
    """Order details page with order-level and item-level status data."""
    order = get_object_or_404(
        Order.objects.prefetch_related("payment", "status"),
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
        .prefetch_related("product_variant__images", "status")
    )

    order_status = order.current_status
    is_cancellable = order_status.status in ("PLACED", "CONFIRMED")

    context = {
        "order": order,
        "items": order_items,
        "order_status_timeline": order.status.all(),
        "gst_rate": settings.GST_RATE,
        "is_cancellable": is_cancellable,
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

    if not order.can_generate_invoice:
        messages.warning(request, "Invoice will be available after order confirmation.")
        return redirect("user_order_details", order_number=order.order_number)

    html_string = render_to_string(
        "orders/user/order_invoice.html",
        {
            "order": order,
            "order_items": order_items,
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


@never_cache
@login_required
def orderitem_detail(request, order_number, item_id):
    """order-item detail"""

    order = get_object_or_404(Order, user=request.user, order_number=order_number)
    order_item = get_object_or_404(
        OrderItem.objects.select_related(
            "order",
            "product_variant",
            "product_variant__product",
            "product_variant__product__brand",
        )
        .select_related("return_request")
        .prefetch_related("status", "transactions", "return_request__transactions"),
        id=item_id,
        order=order,
    )

    timeline = order_item.status.all().order_by("-created_at")
    return_entry = getattr(order_item, "return_request", None)

    context = {
        "order": order,
        "order_item": order_item,
        "timeline": timeline,
        "return_request": return_entry,
    }

    return render(request, "orders/user/orderitem_detail.html", context)
