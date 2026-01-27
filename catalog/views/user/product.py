from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.cache import never_cache
from catalog.models import Product, ProductVariant, Category, Brand


@never_cache
def product_list(request):
    """
    Product listing view (variants-based)
    """

    # GET PARAMETERS
    search = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "")
    selected_categories = request.GET.getlist(
        "category"
    )  # List of                slugs
    selected_brands = request.GET.getlist("brand")  # List of slugs
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
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
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
        "sort_options": sort_options,
        "has_filters": bool(
            selected_categories or selected_brands or min_price or max_price
        ),
    }

    return render(
        request,
        "catalog/user/product/product_list.html",
        context,
    )


@never_cache
def product_detail(request, slug):
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

    # FETCH VARIANTS
    variants = list(
        ProductVariant.objects.filter(
            product=product,
            is_deleted=False,
            is_drafted=False,
        )
        .prefetch_related("images")
        .order_by("-is_featured", "sku")
    )

    if not variants:
        messages.error(request, "This product is currently unavailable.")
        return redirect("product_list")

    # SELECTED VARIANT
    variant_sku = request.GET.get("variant")

    if variant_sku:
        selected_variant = next(
            (v for v in variants if v.sku == variant_sku),
            variants[0],
        )
    else:
        selected_variant = next(
            (v for v in variants if v.is_featured),
            variants[0],
        )

    # VARIANT IMAGES
    variant_images = selected_variant.images.all()

    primary_image = next(
        (img for img in variant_images if img.is_primary),
        variant_images[0] if variant_images else None,
    )

    # STOCK STATUS
    stock = selected_variant.stock

    if stock == 0:
        stock_status = "out_of_stock"
        stock_message = "Out of Stock"
    elif stock <= 5:
        stock_status = "low_stock"
        stock_message = f"Only {stock} left in stock!"
    else:
        stock_status = "in_stock"
        stock_message = "In Stock"

    # PRICING (MODEL-DRIVEN)
    discount_percentage = selected_variant.discount_percentage or 0

    final_price = selected_variant.final_price

    original_price = selected_variant.price if discount_percentage > 0 else None

    # BREADCRUMBS
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

    # STATIC RATINGS & REVIEWS (INTENTIONAL)
    ratings_data = {
        "average": 4.5,
        "total_reviews": 127,
        "distribution": {
            5: 70,
            4: 18,
            3: 8,
            2: 3,
            1: 1,
        },
    }

    reviews = [
        {
            "author": "Michael R.",
            "date": "December 28, 2025",
            "rating": 5,
            "title": "Exceptional Quality",
            "comment": (
                "This watch exceeded all my expectations. "
                "The craftsmanship is outstanding."
            ),
        },
        {
            "author": "Sarah K.",
            "date": "December 15, 2025",
            "rating": 5,
            "title": "Perfect Gift",
            "comment": (
                "Bought this as a gift for my husband and he absolutely loves it."
            ),
        },
    ]

    # RELATED PRODUCTS
    related_products = (
        Product.objects.filter(
            category__in=active_categories,
            is_deleted=False,
            is_drafted=False,
            brand__is_active=True,
        )
        .exclude(id=product.id)
        .prefetch_related("variants")
        .distinct()[:4]
    )

    # SPECIFICATIONS
    specifications = []

    if selected_variant.movement_type:
        specifications.append(("Movement Type", selected_variant.movement_type))
    if selected_variant.case_material:
        specifications.append(("Case Material", selected_variant.case_material))
    if selected_variant.case_size_mm:
        specifications.append(("Case Size", f"{selected_variant.case_size_mm}mm"))
    if selected_variant.dial_color:
        specifications.append(("Dial Color", selected_variant.dial_color))
    if selected_variant.strap_material:
        specifications.append(("Strap Material", selected_variant.strap_material))
    if selected_variant.strap_color:
        specifications.append(("Strap Color", selected_variant.strap_color))

    specifications.append(("SKU", selected_variant.sku))

    # CONTEXT
    context = {
        "product": product,
        "variants": variants,
        "selected_variant": selected_variant,
        "variant_images": variant_images,
        "primary_image": primary_image,
        "stock_status": stock_status,
        "stock_message": stock_message,
        "price": final_price,
        "original_price": original_price,
        "discount_percentage": discount_percentage,
        "breadcrumbs": breadcrumbs,
        "ratings_data": ratings_data,
        "reviews": reviews,
        "related_products": related_products,
        "specifications": specifications,
        "categories": active_categories,
    }

    return render(
        request,
        "catalog/user/product/product_details.html",
        context,
    )
