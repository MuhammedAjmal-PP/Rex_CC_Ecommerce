from catalog.forms import CategoryForm
from catalog.models import Category
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def categories(request):
    """List all categories."""

    # Extract query parameters from request
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    try:
        page_number = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page_number = 1

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
        "form": CategoryForm(),  # Include form for modal
    }

    return render(request, "catalog/admin/category/categories.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def category_add(request):
    """Add a new category via AJAX."""
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            return JsonResponse(
                {
                    "success": True,
                    "message": "Category added successfully.",
                    "category": {
                        "id": category.id,
                        "name": category.name,
                        "slug": category.slug,
                        "is_active": category.is_active,
                    },
                }
            )
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            return JsonResponse({"success": False, "errors": errors}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=405)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def category_edit(request, id):
    """edit a new category via AJAX."""

    category = get_object_or_404(Category, id=id)

    if request.method == "POST":

        form = CategoryForm(request.POST, instance=category)

        if form.is_valid():
            category = form.save()
            return JsonResponse(
                {
                    "success": True,
                    "message": "Category edited successfully.",
                    "category": {
                        "id": category.id,
                        "name": category.name,
                        "slug": category.slug,
                        "is_active": category.is_active,
                    },
                }
            )
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            return JsonResponse({"success": False, "errors": errors}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=405)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def category_status_toggle(request, id):
    """
    category active & deactive

    """

    category = get_object_or_404(Category, id=id)
    category.is_active = not category.is_active
    category.save()

    status_msg = "activated" if category.is_active else "deactivated"
    messages.success(request, f"Category {status_msg} successfully.")

    return redirect(request.META.get("HTTP_REFERER", reverse("admin_categories")))
