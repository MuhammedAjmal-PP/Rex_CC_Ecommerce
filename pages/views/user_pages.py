from django.shortcuts import render
from django.views.decorators.cache import never_cache
from catalog.models import Category, Brand, ProductVariant
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from users.wishlist.utils import get_session_wishlist
from users.wishlist.models import WishlistItem

# Create your views here.



@never_cache
def home(request):
    """
    Homepage view
    """
    categories = Category.objects.filter(is_active=True)

    # Get brands with logos for featured brands section
    brands = Brand.objects.filter(is_active=True, logo__isnull=False)[:5]

    # Get new arrivals - latest 8 variants
    new_arrivals = (
        ProductVariant.objects.filter(
            product__is_drafted=False,
            product__is_deleted=False,
            is_drafted=False,
            is_deleted=False,
            stock__gt=0,
        )
        .select_related("product", "product__brand")
        .prefetch_related("images")
        .order_by("-created_at")[:8]
    )

    # Get featured variants
    featured_variants = (
        ProductVariant.objects.filter(
            product__is_drafted=False,
            product__is_deleted=False,
            is_drafted=False,
            is_deleted=False,
            is_featured=True,
            stock__gt=0,
        )
        .select_related("product", "product__brand")
        .prefetch_related("images")
        .order_by("-created_at")[:8]
    )

    # Get offer variants (variants with active discounts)
    offer_variants = (
        ProductVariant.objects.filter(
            product__is_drafted=False,
            product__is_deleted=False,
            is_drafted=False,
            is_deleted=False,
            stock__gt=0,
            discount_percentage__gt=0,
        )
        .select_related("product", "product__brand")
        .prefetch_related("images")
        .order_by("-discount_percentage")[:8]
    )

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(
            WishlistItem.objects.filter(wishlist__user=request.user).values_list(
                "product_variant_id", flat=True
            )
        )
    else:
        wishlist_ids = get_session_wishlist(request)

    context = {
        "categories": categories,
        "brands": brands,
        "new_arrivals": new_arrivals,
        "featured_variants": featured_variants,
        "offer_variants": offer_variants,
        "wishlist_ids": wishlist_ids,
    }

    return render(request, "pages/user/homepage.html", context)


@require_GET
def get_latest_product(request):
    category_slug = request.GET.get("category")
    brand_slug = request.GET.get("brand")

    variants = (
        ProductVariant.objects.filter(
            product__is_drafted=False,
            product__is_deleted=False,
            is_drafted=False,
            is_deleted=False,
            stock__gt=0,
        )
        .select_related("product", "product__brand")
        .prefetch_related("images")
        .order_by("-created_at")
    )

    if category_slug:
        variants = variants.filter(product__category__slug=category_slug)
    if brand_slug:
        variants = variants.filter(product__brand__slug=brand_slug)

    latest_variant = variants.first()

    if not latest_variant:
        return JsonResponse({"success": False})

    primary_image = latest_variant.images.filter(is_primary=True).first()

    if primary_image:
        image_url = primary_image.image.url
    else:
        image_url = latest_variant.product.thumbnail.url

    return JsonResponse(
        {
            "success": True,
            "variant": {
                "name": latest_variant.product.name,
                "slug": latest_variant.product.slug,
                "brand": latest_variant.product.brand.name,
                "image": image_url,
                "category": latest_variant.product.category.name,
            },
        }
    )
