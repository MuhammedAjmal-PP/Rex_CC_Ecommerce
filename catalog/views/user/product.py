from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from catalog.models import Product, ProductVariant, Category, Brand


def remove_query_param(request, *args):
    params = request.GET.copy()
    for key in args:
        params.pop(key, None)
    return f"?{params.urlencode()}" if params else ""


def product_list(request):
    """
    product listing view on user pages - displays variants
    """
    # Get parameters
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "")
    category = request.GET.get("category", "")
    brand = request.GET.get("brand", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    page_number = request.GET.get("page", 1)

    clear_search_url = remove_query_param(request, "search")

    clear_filter = remove_query_param(
        request,
        "category",
        "brand",
        "min_price",
        "max_price",
    )
    clear_category = remove_query_param(request, "category")
    clear_brand = remove_query_param(request, "brand")
    clear_price = remove_query_param(request, "min_price", "max_price")

    # Get all active variants instead of products
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

    # Search filter
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

    # Category filter
    if category:
        variants = variants.filter(product__category__slug=category)

    # Brand filter
    if brand:
        variants = variants.filter(product__brand__slug=brand)

    # Price filters
    if min_price:
        variants = variants.filter(price__gte=min_price)

    if max_price:
        variants = variants.filter(price__lte=max_price)

    # Sorting
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
        variants = variants.filter(is_featured=True)
    else:
        variants = variants.order_by("-created_at")

    variants = variants.distinct()

    # Pagination
    paginator = Paginator(variants, 15)  # 15 variants for 3 rows x 5 cols
    page_obj = paginator.get_page(page_number)

    # Get filter options
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)

    # Get actual category and brand objects for display
    category_obj = None
    brand_obj = None
    if category:
        category_obj = Category.objects.filter(slug=category, is_active=True).first()
    if brand:
        brand_obj = Brand.objects.filter(slug=brand, is_active=True).first()

    sort_options = [
        ("", "Default"),
        ("price_low", "Price: Low to High"),
        ("price_high", "Price: High to Low"),
        ("az", "Name: A to Z"),
        ("za", "Name: Z to A"),
        ("new", "New Arrivals"),
        ("featured", "Featured"),
    ]


    context = {
        "variants": page_obj,  # Changed from products
        "page_obj": page_obj,
        "categories": categories,
        "brands": brands,
        "search_query": search,
        "category": category,  # slug for form
        "brand": brand,  # slug for form
        "category_obj": category_obj,  # object for display
        "brand_obj": brand_obj,  # object for display
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
        "sort_options": sort_options,
        "has_filters": bool(category or brand or min_price or max_price),
        "clear_search_url": clear_search_url,
        "clear_filter": clear_filter,
        "clear_category": clear_category,
        "clear_brand": clear_brand,
        "clear_price": clear_price,
    }

    return render(request, "catalog/user/product/product_list.html", context)


def product_detail(request, slug):
    """
    Product detail view with comprehensive product information.
    Redirects to product list if product is unavailable or blocked.
    """
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

    # Get all active variants for this product
    variants = (
        ProductVariant.objects.filter(
            product=product,
            is_deleted=False,
            is_drafted=False,
        )
        .prefetch_related("images")
        .order_by("-is_featured", "sku")
    )

    # Check if any variants exist
    if not variants.exists():
        messages.error(request, "This product is currently unavailable.")
        return redirect("product_list")

    # Get the selected variant (from query param or default to first)
    variant_sku = request.GET.get("variant")
    if variant_sku:
        variant = variants.filter(sku=variant_sku).first()
        if not variant:
            variant = variants.first()
    else:
        # Default: first featured variant, or first variant
        variant = variants.filter(is_featured=True).first() or variants.first()

    # Get all images for selected variant
    variant_images = variant.images.all()
    primary_image = variant_images.filter(is_primary=True).first()
    if not primary_image and variant_images.exists():
        primary_image = variant_images.first()

    # Calculate stock status
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

    # Static discount details (mock logic)
    # Assuming the current price is the discounted price, let's fake an original price
    from decimal import Decimal

    discount_percentage = 15  # Static 15% discount
    # Convert percentage math to Decimal to avoid "unsupported operand type(s) for *: 'decimal.Decimal' and 'float'"
    multiplier = Decimal(100) / Decimal(100 - discount_percentage)
    original_price = variant.price * multiplier

    # Build breadcrumbs
    first_category = active_categories.first()
    breadcrumbs = [
        {"name": "Home", "url": "/"},
        {
            "name": first_category.name,
            "url": f"/products/?category={first_category.slug}",
        },
        {"name": product.brand.name, "url": f"/products/?brand={product.brand.slug}"},
        {"name": product.name, "url": None},
    ]

    # Static ratings data
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

    # Static reviews
    static_reviews = [
        {
            "author": "Michael R.",
            "date": "December 28, 2025",
            "rating": 5,
            "title": "Exceptional Quality",
            "comment": "This watch exceeded all my expectations. The craftsmanship is outstanding and it looks even better in person. The attention to detail is remarkable.",
        },
        {
            "author": "Sarah K.",
            "date": "December 15, 2025",
            "rating": 5,
            "title": "Perfect Gift",
            "comment": "Bought this as a gift for my husband and he absolutely loves it. The packaging was premium and the watch itself is stunning.",
        },
    ]

    # Get related products (same category, different product)
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

    # Build specifications
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

    context = {
        "product": product,
        "variants": variants,
        "selected_variant": variant,
        "variant_images": variant_images,
        "primary_image": primary_image,
        "stock_status": stock_status,
        "stock_message": stock_message,
        "original_price": original_price,
        "discount_percentage": discount_percentage,
        "breadcrumbs": breadcrumbs,
        "ratings_data": ratings_data,
        "reviews": static_reviews,
        "related_products": related_products,
        "specifications": specifications,
        "categories": active_categories,
    }

    return render(request, "catalog/user/product/product_details.html", context)
