from django.views.decorators.cache import never_cache
from catalog.models import Product
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from catalog.forms import ProductForm
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
import cloudinary.uploader


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def products(request):
    """List all products."""

    # Extract query parameters from request
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    page_number = request.GET.get("page", 1)

    products = Product.objects.all().order_by("name")

    total_products = products.count()
    published_products = products.filter(is_drafted=False).count()
    drafted_products = products.filter(is_drafted=True).count()
    deleted_products = products.filter(is_deleted=True).count()

    # Apply search filter if query is provided
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(brand__name__icontains=search_query)
        ).distinct()

    # Apply status filter based on draft status
    if status_filter == "published":
        products = products.filter(is_drafted=False)
    elif status_filter == "drafted":
        products = products.filter(is_drafted=True)
    elif status_filter == "deleted":
        products = products.filter(is_deleted=True)

    paginator = Paginator(products, 10)
    page_obj = paginator.get_page(page_number)

    # Prepare context for template rendering
    context = {
        "products": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "total_products": total_products,
        "published_products": published_products,
        "drafted_products": drafted_products,
        "deleted_products": deleted_products,
    }

    return render(request, "catalog/admin/product/products.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def product_add(request):
    """Add a new product."""
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("admin_products")
    else:
        form = ProductForm()
    return render(request, "catalog/admin/product/product_form.html", {"form": form})


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def product_edit(request, id):
    """Edit an existing product."""
    product = get_object_or_404(Product, id=id)

    # Store old thumbnail public_id before form processing
    old_thumbnail = product.thumbnail
    old_thumbnail_public_id = None
    if (
        old_thumbnail
        and hasattr(old_thumbnail, "public_id")
        and old_thumbnail.public_id
    ):
        old_thumbnail_public_id = old_thumbnail.public_id

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            # Check if a new thumbnail was uploaded
            new_thumbnail = request.FILES.get("thumbnail")
            # Check if thumbnail removal was requested
            remove_thumbnail = request.POST.get("remove_thumbnail") == "true"

            # Save the form
            saved_product = form.save(commit=False)

            # Handle thumbnail removal - set to empty string for CloudinaryField
            if remove_thumbnail and not new_thumbnail:
                saved_product.thumbnail = ""

            saved_product.save()
            form.save_m2m()  # Save many-to-many relationships

            # Delete old thumbnail from Cloudinary if new uploaded or removed
            if old_thumbnail_public_id and (new_thumbnail or remove_thumbnail):
                try:
                    cloudinary.uploader.destroy(old_thumbnail_public_id)
                except Exception as e:
                    print(f"Failed to delete old thumbnail from Cloudinary: {e}")

            messages.success(request, "Product updated successfully.")
            return redirect("admin_products")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)
    return render(request, "catalog/admin/product/product_form.html", {"form": form})


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def product_delete_toggle(request, id):
    """Delete a product."""
    product = get_object_or_404(Product, id=id)
    product.is_deleted = not product.is_deleted

    if product.is_deleted:
        product.is_drafted = True
        product.deleted_at = timezone.now()
        status = "deleted"
    else:
        product.deleted_at = None
        status = "restored"
    product.save()
    messages.success(request, f"Product {status} successfully.")
    return redirect(request.META.get("HTTP_REFERER", reverse("admin_products")))


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def product_draft_toggle(request, id):
    """Draft a product."""
    product = get_object_or_404(Product, id=id)
    product.is_drafted = not product.is_drafted
    product.save()
    if product.is_drafted:
        status = "drafted"
    else:
        status = "published"
    messages.success(request, f"Product {status} successfully.")
    return redirect(request.META.get("HTTP_REFERER", reverse("admin_products")))
