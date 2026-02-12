from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from orders.models import Order


@login_required
@never_cache
def order_list(request):
    """Order listing view with search, date filtering, and pagination."""
    search = request.GET.get("q", "").strip()
    date_filter = request.GET.get("date_filter", "").strip().lower()

    orders = Order.objects.filter(user=request.user).prefetch_related("status")

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
    return render(request, "orders/user/orderlist.html", context)


@never_cache
@login_required
def order_detail(request):
    pass


@never_cache
@login_required
def orderitem_detail(request):
    pass
