from ast import arg
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.shortcuts import render
from catalog.models import Product, Category, Brand


def remove_query_param(request, *args):
    params = request.GET.copy()
    for key in args:
        params.pop(key, None)
    return f"?{params.urlencode()}" if params else ""


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

    clear_search_url = remove_query_param(request, "search")
<<<<<<< HEAD

=======
>>>>>>> 489c29e (feat: add active filter chips and polish product list sidebar UI)
    clear_filter = remove_query_param(
        request,
        "category",
        "brand",
        "min_price",
        "max_price",
    )
<<<<<<< HEAD
=======
    clear_category = remove_query_param(request, "category")
    clear_brand = remove_query_param(request, "brand")
    clear_price = remove_query_param(request, "min_price", "max_price")
>>>>>>> 489c29e (feat: add active filter chips and polish product list sidebar UI)

    # Get all active products
    products = (
        Product.objects.filter(
            is_deleted=False,
            is_drafted=False,
            variants__is_deleted=False,
            variants__is_drafted=False,
            variants__stock__gt=0,
            brand__is_active=True,
            category__is_active=True,
        )
        .annotate(
            min_price=Min("variants__price"),
            max_price=Max("variants__price"),
        )
        .distinct()
    )

    # Search filter
    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(brand__name__icontains=search)
            | Q(category__name__icontains=search)
            | Q(variants__sku__icontains=search)
            | Q(variants__dial_color__icontains=search)
            | Q(variants__strap_color__icontains=search)
            | Q(variants__movement_type__icontains=search)
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
    paginator = Paginator(products, 9)
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
        "products": page_obj,
        "page_obj": page_obj,
        "categories": categories,
        "brands": brands,
        "search_query": search,
<<<<<<< HEAD
        "category": category,
        "brand": brand,
=======
        "category": category,  # slug for form
        "brand": brand,  # slug for form
        "category_obj": category_obj,  # object for display
        "brand_obj": brand_obj,  # object for display
>>>>>>> 489c29e (feat: add active filter chips and polish product list sidebar UI)
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
        "sort_options": sort_options,
        "has_filters": bool(category or brand or min_price or max_price),
        "clear_search_url": clear_search_url,
        "clear_filter": clear_filter,
<<<<<<< HEAD
=======
        "clear_category": clear_category,
        "clear_brand": clear_brand,
        "clear_price": clear_price,
>>>>>>> 489c29e (feat: add active filter chips and polish product list sidebar UI)
    }

    return render(request, "catalog/user/product/product_list.html", context)
