from django.core.paginator import Paginator
from django.db.models import Q, Min
from django.shortcuts import render
from catalog.models import Product, Category, Brand


def product_list(request):
    """
    product listing view on user pages
    """
    # Get parameters
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "")
    category = request.GET.get("category", "")
    brand = request.GET.get("brand", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    page_number = request.GET.get("page", 1)

    # Build clear-search URL (keep all filters except search)
    params = request.GET.copy()
    params.pop("search", None)

    clear_search_url = f"?{params.urlencode()}" if params else ""

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

    # Pagination
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
        # "page_obj": page_obj,
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
        "clear_search_url": clear_search_url,
    }

    return render(request, "catalog/user/product/product_list.html", context)
