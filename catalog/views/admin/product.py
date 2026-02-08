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
from catalog.service import manage_product_draft_status


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def products(request):
    """List all products."""

    # Extract query parameters from request
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    try:
        page_number = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page_number = 1

    products = (
        Product.objects.select_related("brand")
        .prefetch_related("category")
        .all()
        .order_by("name")
    )

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
            product = form.save(commit=False)
            product.is_drafted = False
            product.save()
            form.save_m2m()  # Explicitly save many-to-many data
            return redirect("admin_products")
    else:
        form = ProductForm()
    return render(request, "catalog/admin/product/product_form.html", {"form": form})


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def product_edit(request, product_id):
    """Edit an existing product."""
    product = get_object_or_404(Product, id=product_id)

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

    context = {
        "product": product,
        "form": form,
    }
    return render(request, "catalog/admin/product/product_form.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def product_delete_toggle(request, product_id):
    """Delete a product and cascade to variants."""
    product = get_object_or_404(Product, id=product_id)
    product.is_deleted = not product.is_deleted

    if product.is_deleted:
        product.is_drafted = True
        product.deleted_at = timezone.now()
        status = "deleted"
        # Cascade soft-delete to all variants
        product.variants.update(
            is_deleted=True, is_drafted=True, deleted_at=timezone.now()
        )
    else:
        product.deleted_at = None
        status = "restored"
        # Restore variants (but keep them drafted for manual review)
        product.variants.update(is_deleted=False, deleted_at=None)
    product.save()
    messages.success(request, f"Product {status} successfully.")
    return redirect(request.META.get("HTTP_REFERER", reverse("admin_products")))


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def product_draft_toggle(request, product_id):
    """Draft a product."""
    product = get_object_or_404(Product, id=product_id)
    published_variant_count = product.variants.filter(is_drafted=False).count()

    if published_variant_count < 1:
        product.is_drafted = True
        product.save()
        messages.error(
            request,
            "At least one published variant is required to publish this product.",
        )
    else:
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
def product_view(request, product_id):
    """View a product."""
    product = get_object_or_404(Product, id=product_id)

    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    try:
        page_number = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page_number = 1

    variant = product.variants.prefetch_related("images").all()

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

            # Check for at least 3 valid images BEFORE saving anything
            valid_images = []
            primary_count = 0

            for form in imageformset:
                if form.cleaned_data and form.cleaned_data.get("image"):
                    valid_images.append(form)
                    if form.cleaned_data.get("is_primary"):
                        primary_count += 1
            
            if len(valid_images) < 3:
                 messages.error(
                    request,
                    "A minimum of three product images is required to add a variant.",
                )
                 # Re-render the form with errors
                 context = {
                    "variantform": variantform,
                    "imageformset": imageformset,
                    "product": product,
                }
                 return render(request, "catalog/admin/product/variant_form.html", context)

            if primary_count != 1:
                messages.error(request, "Exactly one image must be set as primary.")
                context = {
                    "variantform": variantform,
                    "imageformset": imageformset,
                    "product": product,
                }
                return render(request, "catalog/admin/product/variant_form.html", context)

            variant = variantform.save(commit=False)
            variant.product = product
            variant.save()

            for form in imageformset:
                if form.cleaned_data and form.cleaned_data.get("image"):
                    image = form.save(commit=False)
                    image.variant = variant
                    image.save()

            messages.success(request, "Variant added successfully.")
            return redirect("admin_product_view", product_id=product_id)

    else:
        variantform = ProductVariantForm(initial={"product": product})
        imageformset = ImageFormSet()

    context = {
        "variantform": variantform,
        "imageformset": imageformset,
        "product": product,
    }
    return render(request, "catalog/admin/product/variant_form.html", context)


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
            
            final_image_count = 0
            primary_count = 0

            for form in imageformset:
                if not form.cleaned_data:
                    continue
                
                is_delete = form.cleaned_data.get("DELETE", False)
                has_image = form.cleaned_data.get("image")
                is_primary = form.cleaned_data.get("is_primary", False)
                
                if form.instance.pk:
                    # Existing image
                    if not is_delete:
                        final_image_count += 1
                        if is_primary:
                            primary_count += 1
                else:
                    # New image
                    if has_image:
                        final_image_count += 1
                        if is_primary:
                            primary_count += 1

            if final_image_count < 3:
                messages.error(
                    request,
                    "A minimum of three product images is required. Updates were not saved.",
                )
                context = {
                    "variantform": variantform,
                    "imageformset": imageformset,
                    "product": product,
                    "variant": variant,
                }
                return render(request, "catalog/admin/product/variant_form.html", context)

            if primary_count != 1:
                messages.error(request, "Exactly one image must be set as primary. Updates were not saved.")
                context = {
                    "variantform": variantform,
                    "imageformset": imageformset,
                    "product": product,
                    "variant": variant,
                }
                return render(request, "catalog/admin/product/variant_form.html", context)

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

            manage_product_draft_status(request, product)
            messages.success(request, "Variant updated successfully.")
            return redirect("admin_product_view", product_id=product_id)
    else:
        variantform = ProductVariantForm(instance=variant)
        imageformset = ImageFormset(queryset=images)

    context = {
        "variantform": variantform,
        "imageformset": imageformset,
        "product": product,
        "variant": variant,
    }
    return render(request, "catalog/admin/product/variant_form.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
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
    manage_product_draft_status(request, product)
    return redirect(
        request.META.get(
            "HTTP_REFERER",
            reverse("admin_product_view", kwargs={"product_id": product_id}),
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

    manage_product_draft_status(request, product)

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            reverse("admin_product_view", kwargs={"product_id": product_id}),
        )
    )
