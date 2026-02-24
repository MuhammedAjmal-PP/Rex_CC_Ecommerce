from django.conf import settings
from offers.service import precompute_discounts
from users.cart.models import CartItem

max_purchase_limit = settings.MAX_QUNATITY_PURCHASE_PER_ITEM


def fetch_cart(cart):
    cart_items = (
        CartItem.objects.filter(
            cart=cart,
            product_variant__is_deleted=False,
            product_variant__is_drafted=False,
            product_variant__product__is_deleted=False,
            product_variant__product__is_drafted=False,
        )
        .select_related(
            "product_variant",
            "product_variant__product",
            "product_variant__product__brand",
        )
        .prefetch_related("product_variant__images", "product_variant__product__category")
    )

    return cart_items


def build_cart_summary(cart_items):
    products = []

    # Batch pre-compute discounts for all variants (eliminates N+1 queries)
    variants = [item.product_variant for item in cart_items]
    precompute_discounts(variants)

    for item in cart_items:
        variant = item.product_variant
        image = variant.primary_image

        products.append(
            {
                "variant": {
                    "id": variant.id,
                    "sku": variant.sku,
                    "slug": variant.product.slug,
                    "product_name": variant.product.name,
                    "brand": variant.product.brand.name,
                    "discount_percentage": variant.discount_percentage,
                    "price": variant.price,
                    "final_price": variant.final_price,
                    "stock": variant.stock,
                    "is_in_stock": variant.stock > 0,
                    "image": image.image.url,
                },
                "allowed_max": min(variant.stock, max_purchase_limit),
                "quantity": item.quantity,
                "total_amount": item.total_amount,
                "total_discount": item.total_discount,
            }
        )
    return products
