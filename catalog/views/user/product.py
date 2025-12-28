from django.db.models import Q, Min
from django.shortcuts import render

from catalog.models import Product, Category, Brand


def product_list(request):
    """
    Product listing view with search, sort, and filter functionality.
    All parameters work together in combination.
    """
    # Get filter parameters
    search_query = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "")
    filter_category = request.GET.get("category", "")
    filter_brand = request.GET.get("brand", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")

    # Base queryset - only published products
    products = Product.objects.filter(is_drafted=False, is_deleted=False)

    # Search functionality - search in products and variants
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(brand__name__icontains=search_query)
            | Q(variants__sku__icontains=search_query)
            | Q(variants__dial_color__icontains=search_query)
            | Q(variants__strap_color__icontains=search_query)
            | Q(variants__strap_material__icontains=search_query)
            | Q(variants__case_material__icontains=search_query)
            | Q(variants__movement_type__icontains=search_query)
        ).distinct()

    if filter_category:
        products = products.filter(category__slug=filter_category)

    if filter_brand:
        products = products.filter(brand__slug=filter_brand)

    if min_price:
        try:
            products = products.filter(variants__price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(variants__price__lte=float(max_price))
        except ValueError:
            pass

    products = products.distinct()

    # Sort functionality
    if sort == "price_low":
        products = products.annotate(min_price=Min("variants__price")).order_by(
            "min_price"
        )
    elif sort == "price_high":
        products = products.annotate(min_price=Min("variants__price")).order_by(
            "-min_price"
        )
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

    # Get categories and brands for filter sidebar
    categories = Category.objects.filter(is_active=True).order_by("name")
    brands = Brand.objects.filter(is_active=True).order_by("name")

    # Sort options for template
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
        "products": products,
        "categories": categories,
        "brands": brands,
        "search_query": search_query,
        "sort": sort,
        "sort_options": sort_options,
        "filter_category": filter_category,
        "filter_brand": filter_brand,
        "min_price": min_price,
        "max_price": max_price,
        "has_filters": bool(
            search_query or filter_category or filter_brand or min_price or max_price
        ),
    }

    return render(request, "catalog/user/product/product_list.html", context)
