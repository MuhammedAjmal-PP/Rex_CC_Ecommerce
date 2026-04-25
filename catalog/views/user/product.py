from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.cache import cache_control
from catalog.service import get_category_from_referer
from catalog.models import Product, ProductVariant, Category, Brand
from catalog.utils import pack_variants
from users.wishlist.utils import get_wishlist_variant_ids
from reviews.services import get_product_reviews, get_ratings_summary


@cache_control(no_cache=True, must_revalidate=True, max_age=0)
def product_list(request):
    """
    Product listing view (variants-based)
    """

    # GET PARAMETERS
    search = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "")
    selected_categories = request.GET.getlist("category")
    selected_brands = request.GET.getlist("brand")
    min_price = request.GET.get("min")
    max_price = request.GET.get("max")
    page_number = request.GET.get("page", 1)

    # QUERYSET
    variants = (
        ProductVariant.objects.filter(
            is_deleted=False,
            is_drafted=False,
            product__is_deleted=False,
            product__is_drafted=False,
            product__brand__is_active=True,
            product__category__is_active=True,
        )
        .select_related("product", "product__brand")
        .prefetch_related("images", "product__category")
    )

    # SEARCH
    if search:
        variants = variants.filter(
            Q(product__name__icontains=search)
            | Q(product__brand__name__icontains=search)
            | Q(product__category__name__icontains=search)
            | Q(sku__icontains=search)
            | Q(dial_color__icontains=search)
            | Q(strap_color__icontains=search)
            | Q(movement_type__icontains=search)
        )

    # FILTERS
    if selected_categories:
        variants = variants.filter(product__category__slug__in=selected_categories)

    if selected_brands:
        variants = variants.filter(product__brand__slug__in=selected_brands)

    if min_price:
        variants = variants.filter(price__gte=min_price)

    if max_price:
        variants = variants.filter(price__lte=max_price)

    # SORTING
    if sort == "price_low":
        variants = variants.order_by("price")
    elif sort == "price_high":
        variants = variants.order_by("-price")
    elif sort == "az":
        variants = variants.order_by("product__name")
    elif sort == "za":
        variants = variants.order_by("-product__name")
    elif sort == "new":
        variants = variants.order_by("-created_at")
    elif sort == "featured":
        variants = variants.filter(is_featured=True).order_by("-created_at")
    else:
        variants = variants.order_by("-created_at")

    variants = variants.distinct()

    # PAGINATION
    paginator = Paginator(variants, 15)
    page_obj = paginator.get_page(page_number)

    # Pack the current page's variants (sets primary_image, discount, price)
    pack_variants(page_obj.object_list)

    # FILTER OPTIONS
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)

    sort_options = [
        ("", "Default"),
        ("price_low", "Price: Low to High"),
        ("price_high", "Price: High to Low"),
        ("az", "Name: A to Z"),
        ("za", "Name: Z to A"),
        ("new", "New Arrivals"),
        ("featured", "Featured"),
    ]

    # CONTEXT
    context = {
        "variants": page_obj,
        "page_obj": page_obj,
        "categories": categories,
        "brands": brands,
        "search_query": search,
        "selected_categories": selected_categories,
        "selected_brands": selected_brands,
        "min": min_price,
        "max": max_price,
        "sort": sort,
        "sort_options": sort_options,
        "has_filters": bool(
            selected_categories or selected_brands or min_price or max_price
        ),
        "wishlist_ids": get_wishlist_variant_ids(request),
    }

    return render(
        request,
        "catalog/user/product/product_list.html",
        context,
    )


@cache_control(no_cache=True, must_revalidate=True, max_age=0)
def product_detail(request, slug, sku):
    """
    Product detail page.
    """

    # PRODUCT VALIDATION
    product = get_object_or_404(Product, slug=slug)
    active_categories = product.category.filter(is_active=True)

    if (
        product.is_deleted
        or product.is_drafted
        or not product.brand.is_active
        or not active_categories.exists()
    ):
        messages.error(request, "This product is currently unavailable.")
        return redirect("product_list")

    variants = (
        ProductVariant.objects.filter(
            product=product,
            is_deleted=False,
            is_drafted=False,
        )
        .select_related("product", "product__brand")
        .prefetch_related("images")
        .order_by("-is_featured", "sku")
    )

    if not variants:
        messages.error(request, "This product is currently unavailable.")
        return redirect("product_list")

    # VARIANT — list and pack first, then find selected from the packed list
    variants = list(variants)

    # Pack ALL variants — sets primary_image, discount_percentage, final_price
    pack_variants(variants)

    # Find the selected variant from the packed list (not a fresh DB object)
    variant = next((v for v in variants if v.sku == sku), None)
    if not variant:
        messages.error(request, "This product is currently unavailable.")
        return redirect("product_list")

    # VARIANT IMAGES
    variant_images = variant.images.all()

    primary_image = next(
        (img for img in variant_images if img.is_primary),
        variant_images[0] if variant_images else None,
    )

    # STOCK STATUS
    stock = variant.stock

    if stock == 0:
        stock_status = "out_of_stock"
        stock_message = "Out of Stock"
    elif stock <= 5:
        stock_status = "low_stock"
        stock_message = f"Only {stock} left in stock!"
    else:
        stock_status = "in_stock"
        stock_message = "In Stock"

    # PRICING (set by pack_variants above)
    discount_percentage = variant.discount_percentage or 0
    final_price = variant.final_price
    original_price = variant.price if discount_percentage > 0 else None

    # BREADCRUMBS
    # Try to get category from referrer
    referer_category_slug = get_category_from_referer(request)

    primary_category = None

    if referer_category_slug:
        primary_category = active_categories.filter(slug=referer_category_slug).first()

    # Fallback (important!)
    if not primary_category:
        primary_category = active_categories.first()

    breadcrumbs = [
        {"name": "Home", "url": "/"},
        {
            "name": primary_category.name,
            "url": f"/products/?category={primary_category.slug}",
        },
        {
            "name": product.brand.name,
            "url": f"/products/?brand={product.brand.slug}",
        },
        {"name": product.name, "url": None},
    ]

    # RATINGS & REVIEWS (from reviews app)
    ratings_data = get_ratings_summary(product)
    reviews = get_product_reviews(product)

    # RELATED PRODUCTS — query variants directly to avoid N+1
    related_variants = (
        ProductVariant.objects.filter(
            product__category__in=active_categories,
            product__is_deleted=False,
            product__is_drafted=False,
            product__brand__is_active=True,
            is_deleted=False,
            is_drafted=False,
        )
        .exclude(product_id=product.id)
        .select_related("product", "product__brand")
        .prefetch_related("images")
        .order_by("product_id", "-is_featured")
        .distinct("product_id")[:4]
    )
    related_variants = pack_variants(related_variants)

    # SPECIFICATIONS
    specifications = []

    if variant.movement_type:
        specifications.append(("Movement Type", variant.movement_type))
    if variant.case_material:
        specifications.append(("Case Material", variant.case_material))
    if variant.case_size_mm:
        specifications.append(("Case Size", f"{variant.case_size_mm}mm"))
    if variant.dial_color:
        specifications.append(("Dial Color", variant.dial_color))
    if variant.strap_material:
        specifications.append(("Strap Material", variant.strap_material))
    if variant.strap_color:
        specifications.append(("Strap Color", variant.strap_color))

    specifications.append(("SKU", variant.sku))

    # CONTEXT
    context = {
        "product": product,
        "variants": variants,
        "selected_variant": variant,
        "variant_images": variant_images,
        "primary_image": primary_image,
        "max_qunatity_purchase": settings.MAX_QUANTITY_PURCHASE_PER_ITEM,
        "stock_status": stock_status,
        "stock_message": stock_message,
        "price": final_price,
        "original_price": original_price,
        "discount_percentage": discount_percentage,
        "breadcrumbs": breadcrumbs,
        "ratings_data": ratings_data,
        "reviews": reviews,
        "related_variants": related_variants,
        "specifications": specifications,
        "categories": active_categories,
        "wishlist_ids": get_wishlist_variant_ids(request),
    }

    return render(
        request,
        "catalog/user/product/product_details.html",
        context,
    )
