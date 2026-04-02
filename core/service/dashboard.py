"""
Dashboard analytics service — summary stats, chart data, and best-selling
products / categories / brands.
"""

from decimal import Decimal

from django.db.models import (
    Sum,
    Count,
    F,
    Value,
    CharField,
)
from django.db.models.functions import TruncYear, TruncMonth, TruncWeek, TruncDay
from django.utils import timezone

from accounts.models import CustomUser
from catalog.models import Product
from orders.models import Order, OrderItem

# Statuses that represent a valid, completed-enough order
_EXCLUDED_STATUSES = {"CANCELLED", "FAILED"}

# Also exclude these item statuses from best-selling calculations
_EXCLUDED_ITEM_STATUSES = {"CANCELLED", "RETURNED"}


# ────────────────────────────────────────────
# Summary Stats
# ────────────────────────────────────────────


def get_summary_stats():
    """
    Return headline numbers for the dashboard stat cards.
    """
    order_qs = Order.objects.exclude(status__in=_EXCLUDED_STATUSES)

    agg = order_qs.aggregate(
        total_revenue=Sum("grand_total"),
        total_orders=Count("id"),
    )

    total_customers = CustomUser.objects.filter(
        is_superuser=False, is_staff=False, is_active=True
    ).count()

    total_products = Product.objects.filter(is_deleted=False, is_drafted=False).count()

    return {
        "total_revenue": agg["total_revenue"] or Decimal("0.00"),
        "total_orders": agg["total_orders"] or 0,
        "total_customers": total_customers,
        "total_products": total_products,
    }


# ────────────────────────────────────────────
# Chart Data (Revenue & Orders over time)
# ────────────────────────────────────────────

_TRUNC_MAP = {
    "yearly": TruncYear,
    "monthly": TruncMonth,
    "weekly": TruncWeek,
    "daily": TruncDay,
}

_FORMAT_MAP = {
    "yearly": "%Y",
    "monthly": "%b %Y",
    "weekly": "Week %V, %Y",
    "daily": "%d %b",
}


def get_chart_data(filter_type="monthly"):
    """
    Return revenue and order-count data points grouped by *filter_type*.

    filter_type: 'yearly' | 'monthly' | 'weekly' | 'daily'

    Returns:
        {
            "labels": ["Jan 2025", "Feb 2025", ...],
            "revenue": [12345.00, 23456.00, ...],
            "orders": [10, 22, ...],
        }
    """
    trunc_fn = _TRUNC_MAP.get(filter_type, TruncMonth)
    date_fmt = _FORMAT_MAP.get(filter_type, "%b %Y")

    now = timezone.now()

    # Determine how far back to look
    if filter_type == "yearly":
        start = now.replace(
            year=now.year - 4, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
    elif filter_type == "monthly":
        start = (now - timezone.timedelta(days=365)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    elif filter_type == "weekly":
        start = now - timezone.timedelta(weeks=12)
    else:  # daily
        start = now - timezone.timedelta(days=30)

    qs = (
        Order.objects.exclude(status__in=_EXCLUDED_STATUSES)
        .filter(created_at__gte=start)
        .annotate(period=trunc_fn("created_at"))
        .values("period")
        .annotate(
            revenue=Sum("grand_total"),
            order_count=Count("id"),
        )
        .order_by("period")
    )

    labels = []
    revenue = []
    orders = []

    for row in qs:
        labels.append(row["period"].strftime(date_fmt))
        revenue.append(float(row["revenue"] or 0))
        orders.append(row["order_count"] or 0)

    return {"labels": labels, "revenue": revenue, "orders": orders}


# ────────────────────────────────────────────
# Best-Selling Products (Top N)
# ────────────────────────────────────────────


def get_top_products(limit=10):
    """
    Top products by total quantity sold.

    Returns list of dicts:
        [{"name": "...", "total_qty": 42, "total_revenue": 12345.00}, ...]
    """
    return list(
        OrderItem.objects.exclude(status__in=_EXCLUDED_ITEM_STATUSES)
        .exclude(order__status__in=_EXCLUDED_STATUSES)
        .values(name=F("product_variant__product__name"))
        .annotate(
            total_qty=Sum("quantity"),
            total_revenue=Sum(F("price") * F("quantity")),
        )
        .order_by("-total_qty")[:limit]
    )


# ────────────────────────────────────────────
# Best-Selling Categories (Top N)
# ────────────────────────────────────────────


def get_top_categories(limit=10):
    """
    Top categories by total quantity sold.

    Product has a ManyToMany to Category, so one item can
    contribute to multiple categories.
    """
    return list(
        OrderItem.objects.exclude(status__in=_EXCLUDED_ITEM_STATUSES)
        .exclude(order__status__in=_EXCLUDED_STATUSES)
        .values(name=F("product_variant__product__category__name"))
        .annotate(
            total_qty=Sum("quantity"),
            total_revenue=Sum(F("price") * F("quantity")),
        )
        .exclude(name__isnull=True)
        .order_by("-total_qty")[:limit]
    )


# ────────────────────────────────────────────
# Best-Selling Brands (Top N)
# ────────────────────────────────────────────


def get_top_brands(limit=10):
    """
    Top brands by total quantity sold.
    """
    return list(
        OrderItem.objects.exclude(status__in=_EXCLUDED_ITEM_STATUSES)
        .exclude(order__status__in=_EXCLUDED_STATUSES)
        .values(name=F("product_variant__product__brand__name"))
        .annotate(
            total_qty=Sum("quantity"),
            total_revenue=Sum(F("price") * F("quantity")),
        )
        .exclude(name__isnull=True)
        .order_by("-total_qty")[:limit]
    )
