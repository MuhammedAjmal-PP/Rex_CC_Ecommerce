from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from orders.models import Order

# Statuses that represent a "successful" order
_EXCLUDED_STATUSES = {"CANCELLED", "FAILED"}


# ────────────────────────────────────────────
# Date-range helper
# ────────────────────────────────────────────


def get_date_range(filter_type, start_date=None, end_date=None):
    """
    Return (start_datetime, end_datetime) based on the quick-filter type.

    filter_type:
        'all'     – all time (earliest possible → now)
        '1_day'   – today (start of day → now)
        '1_week'  – last 7 days
        '1_month' – last 30 days
        'custom'  – use the provided start_date / end_date
    """
    now = timezone.now()

    if filter_type == "all":
        start = timezone.make_aware(timezone.datetime(2000, 1, 1))
        return start, now

    if filter_type == "1_day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now

    if filter_type == "1_week":
        return now - timedelta(days=7), now

    if filter_type == "1_month":
        return now - timedelta(days=30), now

    if filter_type == "custom" and start_date and end_date:
        return start_date, end_date

    # Default: today
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


# ────────────────────────────────────────────
# Aggregation
# ────────────────────────────────────────────


def get_sales_report(start_dt, end_dt):
    """
    Aggregate order data between start_dt and end_dt.

    Returns a dict with:
        total_orders, total_order_amount, total_discount,
        total_coupon_discount, orders_qs (filtered queryset).
    """
    orders_qs = (
        Order.objects.filter(created_at__range=(start_dt, end_dt))
        .select_related("user", "coupon")
        .prefetch_related("payment")
        .exclude(status__in=_EXCLUDED_STATUSES)
        .order_by("-created_at")
    )

    aggregates = orders_qs.aggregate(
        total_orders=Count("id"),
        total_order_amount=Sum("grand_total"),
        total_discount=Sum("discount"),
        total_coupon_discount=Sum("coupon_discount"),
    )

    return {
        "total_orders": aggregates["total_orders"] or 0,
        "total_order_amount": aggregates["total_order_amount"] or Decimal("0.00"),
        "total_discount": aggregates["total_discount"] or Decimal("0.00"),
        "total_coupon_discount": aggregates["total_coupon_discount"] or Decimal("0.00"),
        "orders_qs": orders_qs,
    }
