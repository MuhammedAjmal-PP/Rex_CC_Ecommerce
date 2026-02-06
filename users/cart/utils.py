from decimal import Decimal
from users.cart.models import CartItem


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
        .prefetch_related("product_variant__images")
    )

    return cart_items


def build_cart_summary(cart_items):
    products = []
    products_total_price = Decimal("0.00")

    for item in cart_items:
        variant = item.product_variant
        image = variant.images.filter(is_primary=True).first()

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
                "quantity": item.quantity,
                "total_amount": variant.final_price * item.quantity,
                "total_discount": variant.discount_amount * item.quantity,
            }
        )
        products_total_price += variant.final_price * item.quantity
    return products, products_total_price
