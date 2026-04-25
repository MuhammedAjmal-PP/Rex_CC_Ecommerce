from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from accounts.decorators import superuser_required
from django.contrib import messages

from coupons.forms import CouponForm
from coupons.models import Coupon




@never_cache
@superuser_required
def coupon_list(request):
    """Admin coupon list with search, filtering, and pagination."""
    coupons = Coupon.active.all().order_by("-created_at")

    search_query = request.GET.get("q", "").strip()
    if search_query:
        coupons = coupons.filter(
            Q(code__icontains=search_query) | Q(description__icontains=search_query)
        ).distinct()

    # ── Filter: status ───────────────────────────
    status_filter = request.GET.get("status", "").strip()
    now = timezone.now()
    if status_filter == "active":
        coupons = coupons.filter(is_active=True)
    elif status_filter == "inactive":
        coupons = coupons.filter(is_active=False)
    elif status_filter == "valid":
        coupons = coupons.filter(is_active=True, start_date__lte=now, end_date__gte=now)
    elif status_filter == "expired":
        coupons = coupons.filter(end_date__lt=now)

    # ── Filter: discount type ────────────────────
    discount_type = request.GET.get("discount_type", "").strip()
    if discount_type:
        coupons = coupons.filter(discount_type=discount_type)

    # ── Stats ────────────────────────────────────
    all_coupons = Coupon.active.all()
    total_coupons = all_coupons.count()
    active_coupons = all_coupons.filter(is_active=True).count()
    inactive_coupons = all_coupons.filter(is_active=False).count()
    valid_coupons = all_coupons.filter(
        is_active=True, start_date__lte=now, end_date__gte=now
    ).count()
    expired_coupons = all_coupons.filter(end_date__lt=now).count()

    # ── Pagination ───────────────────────────────
    paginator = Paginator(coupons, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "coupons": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "selected_discount_type": discount_type,
        "discount_type_choices": Coupon.DISCOUNT_TYPE_CHOICES,
        "total_coupons": total_coupons,
        "active_coupons": active_coupons,
        "inactive_coupons": inactive_coupons,
        "valid_coupons": valid_coupons,
        "expired_coupons": expired_coupons,
    }
    return render(request, "coupons/admin/coupon_list.html", context)


@never_cache
@superuser_required
def add_coupon(request):
    """Create a new coupon."""
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon created successfully.")
            return redirect("admin_coupons")
    else:
        form = CouponForm()
    return render(request, "coupons/admin/coupon_form.html", {"form": form})


@never_cache
@superuser_required
def edit_coupon(request, pk):
    """Edit an existing coupon."""
    coupon = get_object_or_404(Coupon, pk=pk)
    if request.method == "POST":
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon updated successfully.")
            return redirect("admin_coupons")
    else:
        form = CouponForm(instance=coupon)
    return render(
        request, "coupons/admin/coupon_form.html", {"form": form, "coupon": coupon}
    )


@never_cache
@superuser_required
def delete_coupon(request, pk):
    """Soft-delete a coupon (POST-only)."""
    if request.method == "POST":
        coupon = get_object_or_404(Coupon, pk=pk)
        coupon.soft_delete()
        messages.success(request, "Coupon deleted.")
    return redirect("admin_coupons")
