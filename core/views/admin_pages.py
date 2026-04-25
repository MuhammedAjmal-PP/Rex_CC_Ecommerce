from django.http import JsonResponse
from django.shortcuts import render
from accounts.decorators import superuser_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from core.service.dashboard import (
    get_summary_stats,
    get_chart_data,
    get_top_products,
    get_top_categories,
    get_top_brands,
)


@never_cache
@superuser_required
def admin_dashboard(request):
    context = {
        "summary": get_summary_stats(),
        "top_products": get_top_products(10),
        "top_categories": get_top_categories(10),
        "top_brands": get_top_brands(10),
    }
    return render(request, "core/admin/dashboard.html", context)


@never_cache
@superuser_required
@require_GET
def dashboard_chart_data(request):
    """JSON endpoint for the dashboard chart (called via AJAX)."""
    filter_type = request.GET.get("filter", "monthly").strip()
    if filter_type not in ("yearly", "monthly", "weekly", "daily"):
        filter_type = "monthly"

    data = get_chart_data(filter_type)
    return JsonResponse(data)
