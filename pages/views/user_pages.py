from django.shortcuts import render
from catalog.models import Category, Brand, Product, ProductVariant, ProductImage
from django.db.models import Q


# Create your views here.


def home(request):

    search_query = request.GET.get("search", "").strip()

    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    products = Product.objects.filter(is_drafted=False)

    if search_query:
        brands = brands.filter(name__icontains=search_query).distinct()
        categories = categories.filter(name__icontains=search_query).distinct()
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(brand__name__icontains=search_query)
        ).distinct()

    context = {
        "categories": categories,
        "brands": brands,
        "products": products,
    }

    return render(request, "pages/user/homepage.html", context)
