from django.shortcuts import render
from catalog.models import Category, Brand, Product, ProductVariant
from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_GET


# Create your views here.


def home(request):
    """
    Homepage view
    """
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    products = Product.objects.filter(is_drafted=False, is_deleted=False)
    products = Product.objects.prefetch_related(
        Prefetch(
            "variants",
            queryset=ProductVariant.objects.order_by("-created_at"),
            to_attr="ordered_variants",
        )
    )

    context = {
        "categories": categories,
        "brands": brands,
        "products": products,
    }

    return render(request, "pages/user/homepage.html", context)


@require_GET
def get_latest_product(request):
    """
    AJAX endpoint to get the latest product variant by category or brand
    Returns variant information including color, size, price, and product details
    """
    category_slug = request.GET.get('category')
    brand_slug = request.GET.get('brand')
    
    # Base queryset for active variants
    variants = ProductVariant.objects.filter(
        product__is_active=True,
        is_active=True,
        stock__gt=0
    ).select_related('product', 'product__brand', 'color', 'size').order_by('-created_at')
    
    # Filter by category if provided
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            variants = variants.filter(product__category=category)
        except Category.DoesNotExist:
            pass
    
    # Filter by brand if provided
    if brand_slug:
        try:
            brand = Brand.objects.get(slug=brand_slug)
            variants = variants.filter(product__brand=brand)
        except Brand.DoesNotExist:
            pass
    
    # Get the latest variant
    latest_variant = variants.first()
    
    if latest_variant:
        # Get variant image or fallback to product thumbnail
        variant_image = None
        if latest_variant.images.exists():
            variant_image = latest_variant.images.first().image.url
        elif latest_variant.product.thumbnail:
            variant_image = latest_variant.product.thumbnail.url
        
        return JsonResponse({
            'success': True,
            'variant': {
                'id': latest_variant.id,
                'sku': latest_variant.sku,
                'name': latest_variant.product.name,
                'slug': latest_variant.product.slug,
                'price': str(latest_variant.price),
                'final_price': str(latest_variant.final_price),
                'discount_percentage': latest_variant.discount_percentage,
                'color': latest_variant.color.name if latest_variant.color else None,
                'size': latest_variant.size.name if latest_variant.size else None,
                'thumbnail': variant_image,
                'stock': latest_variant.stock,
            }
        })
    
    return JsonResponse({
        'success': False,
        'message': 'No variants found'
    })
