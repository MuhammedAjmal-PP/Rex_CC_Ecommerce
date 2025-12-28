from django.shortcuts import render
from catalog.models import Category, Brand, Product, ProductVariant, ProductImage
from django.db.models import Q


# Create your views here.


def home(request):
    """
    Homepage view - displays featured products, categories, and brands.
    Search is handled by the product list page via navigation.
    """
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    products = Product.objects.filter(is_drafted=False, is_deleted=False)

    context = {
        "categories": categories,
        "brands": brands,
        "products": products,
    }

    return render(request, "pages/user/homepage.html", context)
