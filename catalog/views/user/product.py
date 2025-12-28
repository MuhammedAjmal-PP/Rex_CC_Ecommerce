from django.core.paginator import Paginator
from django.db.models import Q, Min
from django.shortcuts import render

from catalog.models import Product, Category, Brand


def product_list(request):
    # Get URL parameters
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "")
    category = request.GET.get("category", "")
    brand = request.GET.get("brand", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    page_number = request.GET.get("page", 1)

    # Get all active products
    products = Product.objects.filter(is_drafted=False, is_deleted=False)

    # Search filter
    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(brand__name__icontains=search)
            | Q(category__name__icontains=search)
        )

    # Category filter
    if category:
        products = products.filter(category__slug=category)

    # Brand filter
    if brand:
        products = products.filter(brand__slug=brand)

    # Price filters
    if min_price:
        products = products.filter(variants__price__gte=min_price)

    if max_price:
        products = products.filter(variants__price__lte=max_price)

    # Remove duplicates
    products = products.distinct()

    # Sorting
    if sort == "price_low":
        products = products.annotate(price=Min("variants__price")).order_by("price")
    elif sort == "price_high":
        products = products.annotate(price=Min("variants__price")).order_by("-price")
    elif sort == "az":
        products = products.order_by("name")
    elif sort == "za":
        products = products.order_by("-name")
    elif sort == "new":
        products = products.order_by("-created_at")
    elif sort == "featured":
        products = products.filter(variants__is_featured=True).distinct()
    else:
        products = products.order_by("-created_at")

    # Pagination - 12 products per page
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(page_number)

    # Get filter options
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

    context = {
        "products": page_obj,
        "page_obj": page_obj,
        "categories": categories,
        "brands": brands,
        "search_query": search,
        "filter_category": category,
        "filter_brand": brand,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
        "sort_options": sort_options,
        "has_filters": bool(search or category or brand or min_price or max_price),
    }

    return render(request, "catalog/user/product/product_list.html", context)


def product_detail(request, slug):
    # Get product or redirect if not available
    try:
        product = Product.objects.get(slug=slug, is_drafted=False, is_deleted=False)
    except Product.DoesNotExist:
        from django.shortcuts import redirect
        from django.contrib import messages

        messages.error(request, "Product is unavailable or has been removed.")
        return redirect("product_list")

    # Check if brand is active
    if not product.brand.is_active:
        from django.shortcuts import redirect
        from django.contrib import messages

        messages.error(request, "This product is currently unavailable.")
        return redirect("product_list")

    # Get variant from URL or first available
    variant_sku = request.GET.get("variant", "")
    variants = product.variants.filter(is_drafted=False, is_deleted=False)

    if variant_sku:
        selected_variant = variants.filter(sku=variant_sku).first()
    else:
        selected_variant = variants.first()

    # If no variant available
    if not selected_variant:
        from django.shortcuts import redirect
        from django.contrib import messages

        messages.error(request, "This product is currently out of stock.")
        return redirect("product_list")

    # Get variant images
    variant_images = selected_variant.images.all()
    primary_image = variant_images.filter(is_primary=True).first()
    if not primary_image:
        primary_image = variant_images.first()

    # Get stock status
    stock = selected_variant.stock
    if stock == 0:
        stock_status = "out_of_stock"
        stock_label = "Out of Stock"
    elif stock <= 5:
        stock_status = "low_stock"
        stock_label = f"Only {stock} left!"
    else:
        stock_status = "in_stock"
        stock_label = "In Stock"

    # Get categories for breadcrumb
    categories = product.category.filter(is_active=True)
    first_category = categories.first()

    # Related products (same category, exclude current)
    related_products = (
        Product.objects.filter(
            category__in=categories, is_drafted=False, is_deleted=False
        )
        .exclude(id=product.id)
        .distinct()[:4]
    )

    # Static ratings data
    ratings = {
        "average": 4.5,
        "total": 128,
        "stars": [
            {"value": 5, "percent": 65},
            {"value": 4, "percent": 20},
            {"value": 3, "percent": 10},
            {"value": 2, "percent": 3},
            {"value": 1, "percent": 2},
        ],
    }

    # Static reviews
    reviews = [
        {
            "author": "Rahul M.",
            "date": "Dec 15, 2024",
            "rating": 5,
            "title": "Excellent timepiece!",
            "content": "The watch exceeded my expectations. Build quality is superb and it looks even better in person.",
        },
        {
            "author": "Priya S.",
            "date": "Dec 10, 2024",
            "rating": 4,
            "title": "Great value for money",
            "content": "Beautiful design and comfortable to wear. Delivery was quick and packaging was premium.",
        },
    ]

    # Static coupons
    coupons = [
        {"code": "FIRST10", "discount": "10% off on first order"},
        {"code": "LUXURY15", "discount": "15% off on orders above ₹50,000"},
    ]

    # Product highlights/specs
    highlights = [
        {"label": "Dial Color", "value": selected_variant.dial_color or "-"},
        {"label": "Strap Color", "value": selected_variant.strap_color or "-"},
        {"label": "Strap Material", "value": selected_variant.strap_material or "-"},
        {"label": "Case Material", "value": selected_variant.case_material or "-"},
        {"label": "Movement", "value": selected_variant.movement_type or "-"},
        {
            "label": "Case Size",
            "value": (
                f"{selected_variant.case_size_mm}mm"
                if selected_variant.case_size_mm
                else "-"
            ),
        },
    ]

    context = {
        "product": product,
        "variant": selected_variant,
        "variants": variants,
        "variant_images": variant_images,
        "primary_image": primary_image,
        "stock_status": stock_status,
        "stock_label": stock_label,
        "stock_count": stock,
        "first_category": first_category,
        "related_products": related_products,
        "ratings": ratings,
        "reviews": reviews,
        "coupons": coupons,
        "highlights": highlights,
    }

    return render(request, "catalog/user/product/product_detail.html", context)
