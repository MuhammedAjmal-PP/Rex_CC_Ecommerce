from django.shortcuts import render, redirect
from catalog.forms import BrandForm
from catalog.models import Brand
from django.core.paginator import Paginator
from django.contrib import messages


# Create your views here.


def brand_list(request):
    """List all brands."""

    # Extract query parameters from request
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    page_number = request.GET.get("page", 1)

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


def brand_add(request):
    """Add a new brand."""
    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Brand added successfully.")
                return redirect("admin_brands")
            except form.IntegrityError:
                return render(
                    request, "catalog/admin/brand/brand_add.html", {"form": form}
                )
        else:
            messages.error(request, "Failed to add brand.")
    else:
        form = BrandForm()
    return render(request, "catalog/admin/brand/brand_add.html", {"form": form})
