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
    
    # Get brands with logos for featured brands section
    brands = Brand.objects.filter(is_active=True, logo__isnull=False)[:5]
    
    # Get the latest variant for initial mega menu display
    latest_variant = ProductVariant.objects.filter(
        product__is_drafted=False,
        product__is_deleted=False,
        is_drafted=False,
        is_deleted=False,
        stock__gt=0
    ).select_related('product', 'product__brand').prefetch_related('images').order_by('-created_at').first()

    # Get new arrivals - latest 8 variants
    new_arrivals = ProductVariant.objects.filter(
        product__is_drafted=False,
        product__is_deleted=False,
        is_drafted=False,
        is_deleted=False,
        stock__gt=0
    ).select_related('product', 'product__brand').prefetch_related('images').order_by('-created_at')[:8]
    
    # Get featured variants
    featured_variants = ProductVariant.objects.filter(
        product__is_drafted=False,
        product__is_deleted=False,
        is_drafted=False,
        is_deleted=False,
        is_featured=True,
        stock__gt=0
    ).select_related('product', 'product__brand').prefetch_related('images').order_by('-created_at')[:8]
    
    # Get offer variants (variants with active discounts)
    offer_variants = ProductVariant.objects.filter(
        product__is_drafted=False,
        product__is_deleted=False,
        is_drafted=False,
        is_deleted=False,
        stock__gt=0,
        discount_percentage__gt=0
    ).select_related('product', 'product__brand').prefetch_related('images').order_by('-discount_percentage')[:8]

    context = {
        "categories": categories,
        "brands": brands,
        "latest_variant": latest_variant,
        "new_arrivals": new_arrivals,
        "featured_variants": featured_variants,
        "offer_variants": offer_variants,
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
        product__is_drafted=False,
        product__is_deleted=False,
        is_drafted=False,
        is_deleted=False,
        stock__gt=0
    ).select_related('product', 'product__brand').order_by('-created_at')
    
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
            variant_image = latest_variant.images.filter(is_primary=True)
        elif latest_variant.product.thumbnail:
            variant_image = latest_variant.product.thumbnail.url
        
        return JsonResponse({
            'success': True,
            'variant': {
                'name': latest_variant.product.name,
                'slug': latest_variant.product.slug,
                'discount_percentage': latest_variant.discount_percentage,
                'thumbnail': variant_image,
            }
        })
    
    return JsonResponse({
        'success': False,
        'message': 'No variants found'
    })
