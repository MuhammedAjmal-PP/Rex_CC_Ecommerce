from catalog.models import Category
from django.core.paginator import Paginator
from django.shortcuts import render


def categories(request):
    """List all categories."""

    # Extract query parameters from request
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    page_number = request.GET.get("page", 1)

    categories = Category.objects.all().order_by("name")

    # Apply search filter if query is provided
    if search_query:
        categories = categories.filter(name__icontains=search_query)

    # Apply status filter based on category selection
    if status_filter == "active":
        categories = categories.filter(is_active=True)
    elif status_filter == "inactive":
        categories = categories.filter(is_active=False)

    paginator = Paginator(categories, 10)
    page_obj = paginator.get_page(page_number)

    # Prepare context for template rendering
    context = {
        "categories": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
    }

    return render(request, "catalog/admin/category/categories.html", context)
