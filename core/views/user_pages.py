from django.shortcuts import render
from django.views.decorators.cache import never_cache
from catalog.models import Category, Brand, ProductVariant, Product
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from users.wishlist.utils import get_session_wishlist
from users.wishlist.models import WishlistItem
from offers.service import get_offer_variants

# Create your views here.


@never_cache
def home(request):
    """
    Homepage view
    """
    categories = Category.objects.filter(is_active=True)

    # Get brands with logos for featured brands section
    brands = Brand.objects.filter(is_active=True, logo__isnull=False)[:5]

    product_variant = (
        ProductVariant.objects.filter(
            product__is_drafted=False,
            product__is_deleted=False,
            is_drafted=False,
            is_deleted=False,
            stock__gt=0,
        )
        .select_related("product", "product__brand")
        .prefetch_related("images")
    )

    new_arrivals = product_variant.order_by("-created_at")[:8]

    featured_variants = product_variant.filter(is_featured=True).order_by(
        "-created_at"
    )[:8]

    offer_variants = get_offer_variants(product_variant, limit=8)

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

    return render(request, "core/user/homepage.html", context)


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
                "sku": latest_variant.sku,
            },
        }
    )


@require_GET
def get_mega_menu_data(request):
    """
    API to fetch Categories and Top Brands for the Mega Menu.
    Used for global access across all pages.
    """
    categories = list(
        Category.objects.filter(is_active=True).values("name", "slug")[:5]
    )

    brands = list(
        Brand.objects.filter(is_active=True, logo__isnull=False).values("name", "slug")[
            :6
        ]
    )

    return JsonResponse({"success": True, "categories": categories, "brands": brands})
