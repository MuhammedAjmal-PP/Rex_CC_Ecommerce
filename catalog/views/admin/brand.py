from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from catalog.forms import BrandForm
from catalog.models import Brand
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test

# Create your views here.


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def brands(request):
    """List all brands."""

    # Extract query parameters from request
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    try:
        page_number = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page_number = 1

    brands = Brand.objects.all().order_by("name")

    # Apply search filter if query is provided
    if search_query:
        brands = brands.filter(name__icontains=search_query)

    # Apply status filter based on brand selection
    if status_filter == "active":
        brands = brands.filter(is_active=True)
    elif status_filter == "inactive":
        brands = brands.filter(is_active=False)

    paginator = Paginator(brands, 10)
    page_obj = paginator.get_page(page_number)

    # Prepare context for template rendering
    context = {
        "brands": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
    }

    return render(request, "catalog/admin/brand/brand.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def brand_add(request):
    """Add a new brand."""
    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand added successfully.")
            return redirect("admin_brands")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BrandForm()
    return render(request, "catalog/admin/brand/brand_form.html", {"form": form})


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def brand_edit(request, id):
    """Edit a brand."""
    brand = get_object_or_404(Brand, id=id)

    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand updated successfully.")
            return redirect("admin_brands")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BrandForm(instance=brand)
    return render(request, "catalog/admin/brand/brand_form.html", {"form": form})


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def brand_status_toggle(request, id):
    """
    brand active & deactive

    """

    brand = get_object_or_404(Brand, id=id)
    brand.is_active = not brand.is_active
    brand.save()

    status_msg = "activated" if brand.is_active else "deactivated"
    messages.success(request, f"Brand {status_msg} successfully.")

    return redirect(request.META.get("HTTP_REFERER", reverse("admin_brands")))


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def brand_view(request, id):
    """
    view details of brand
    """
    brand = get_object_or_404(Brand, id=id)

    context = {"brand": brand}

    return render(request, "catalog/admin/brand/brand_view.html", context)
