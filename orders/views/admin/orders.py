from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from orders.models import Order


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
def order_list(request):
    search_query = request.GET.get("qs", "").strip()
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
            if order.current_status.status == status_filter
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
def order_detail(request):
    pass
