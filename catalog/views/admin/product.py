from django.views.decorators.cache import never_cache
from catalog.models import Product, ProductVariant, ProductImage
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from catalog.forms import ProductForm, ProductVariantForm, ProductImageForm
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.forms import formset_factory, modelformset_factory


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

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
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


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def product_view(request, id):
    """View a product."""
    product = get_object_or_404(Product, id=id)

    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    page_number = request.GET.get("page", 1)

    variant = product.variants.all()

    total_variants = variant.count()
    published_variants = variant.filter(is_drafted=False).count()
    drafted_variants = variant.filter(is_drafted=True).count()
    deleted_variants = variant.filter(is_deleted=True).count()
    featured_variants = variant.filter(is_featured=True).count()

    if search_query:
        variant = variant.filter(
            Q(sku__icontains=search_query)
            | Q(dial_color__icontains=search_query)
            | Q(strap_color__icontains=search_query)
            | Q(strap_material__icontains=search_query)
            | Q(case_material__icontains=search_query)
            | Q(movement_type__icontains=search_query)
            | Q(case_size_mm__icontains=search_query)
        ).distinct()

    if status_filter == "published":
        variant = variant.filter(is_drafted=False)
    elif status_filter == "drafted":
        variant = variant.filter(is_drafted=True)
    elif status_filter == "deleted":
        variant = variant.filter(is_deleted=True)
    elif status_filter == "featured":
        variant = variant.filter(is_featured=True)

    paginator = Paginator(variant, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        "product": product,
        "variant": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "total_variants": total_variants,
        "published_variants": published_variants,
        "drafted_variants": drafted_variants,
        "deleted_variants": deleted_variants,
        "featured_variants": featured_variants,
    }

    return render(request, "catalog/admin/product/product_view.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def variant_add(request, product_id):
    """Add a new variant."""
    product = get_object_or_404(Product, id=product_id)

    extraimg = int(request.GET.get("extra", 0))

    ImageFormSet = formset_factory(ProductImageForm, min_num=3, extra=extraimg)

    if request.method == "POST":
        variantform = ProductVariantForm(request.POST)
        imageformset = ImageFormSet(request.POST, request.FILES)

        if variantform.is_valid() and imageformset.is_valid():
            variant = variantform.save(commit=False)
            variant.product = product
            variant.save()

            for form in imageformset:
                # Only save if an image was actually uploaded
                if form.cleaned_data and form.cleaned_data.get("image"):
                    image = form.save(commit=False)
                    image.variant = variant
                    image.save()

            messages.success(request, "Variant created successfully.")
            return redirect("admin_product_view", id=id)

    else:
        variantform = ProductVariantForm(initial={"product": product})
        imageformset = ImageFormSet()

    context = {
        "variantform": variantform,
        "imageformset": imageformset,
        "product": product,
    }
    return render(request, "catalog/admin/product/variant_add_form.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def variant_edit(request, product_id, variant_id):
    """Edit an existing variant."""
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, product=product, id=variant_id)
    images = variant.images.all()

    extraimg = int(request.GET.get("extra", 0))

    ImageFormset = modelformset_factory(
        ProductImage,
        form=ProductImageForm,
        min_num=3,
        extra=extraimg,
        can_delete=True,  # Enable deletion of existing images
    )

    if request.method == "POST":
        variantform = ProductVariantForm(request.POST, instance=variant)
        imageformset = ImageFormset(request.POST, request.FILES, queryset=images)

        if variantform.is_valid() and imageformset.is_valid():
            variant = variantform.save(commit=False)
            variant.product = product
            variant.save()

            for form in imageformset:
                if form.cleaned_data:
                    # Handle deletion of existing images
                    if form.cleaned_data.get("DELETE") and form.instance.pk:
                        form.instance.delete()
                    # Save new images
                    elif form.cleaned_data.get("image"):
                        image = form.save(commit=False)
                        image.variant = variant
                        image.save()

            messages.success(request, "Variant updated successfully.")
            return redirect("admin_product_view", id=product_id)
    else:
        variantform = ProductVariantForm(instance=variant)
        imageformset = ImageFormset(queryset=images)

    context = {
        "variantform": variantform,
        "imageformset": imageformset,
        "product": product,
        "variant": variant,
    }
    return render(request, "catalog/admin/product/variant_edit_form.html", context)


def variant_view(request, product_id, variant_id):
    """
    view details of view
    """
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, product=product, id=variant_id)
    images = variant.images.all()

    context = {
        "product": product,
        "variant": variant,
        "images": images,
    }

    return render(request, "catalog/admin/product/variant_view.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def variant_delete_toggle(request, product_id, variant_id):
    """Toggle delete status for a variant."""
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, product=product, id=variant_id)
    variant.is_deleted = not variant.is_deleted

    if variant.is_deleted:
        variant.is_drafted = True
        variant.deleted_at = timezone.now()
        status = "deleted"
    else:
        variant.deleted_at = None
        status = "restored"
    variant.save()
    messages.success(request, f"Variant {status} successfully.")
    return redirect(
        request.META.get(
            "HTTP_REFERER", reverse("admin_product_view", kwargs={"id": product_id})
        )
    )


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def variant_draft_toggle(request, product_id, variant_id):
    """Toggle draft status for a variant."""
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, product=product, id=variant_id)
    variant.is_drafted = not variant.is_drafted
    variant.save()
    if variant.is_drafted:
        status = "drafted"
    else:
        status = "published"
    messages.success(request, f"Variant {status} successfully.")
    return redirect(
        request.META.get(
            "HTTP_REFERER", reverse("admin_product_view", kwargs={"id": product_id})
        )
    )
