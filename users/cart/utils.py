from decimal import Decimal
from django.conf import settings
from catalog.utils import pack_variants
from users.cart.models import CartItem

max_purchase_limit = settings.MAX_QUNATITY_PURCHASE_PER_ITEM


def fetch_cart(cart):
    """Fetch cart items with all necessary related data prefetched."""
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
        .prefetch_related(
            "product_variant__images", "product_variant__product__category"
        )
    )

    return cart_items


def compute_cart_summary(cart):
    """
    Single function that fetches items, packs variants, and computes
    every cart total. Returns a dict with all data views/templates need.

    Usage:
        summary = compute_cart_summary(cart)
        summary["items_count"]   # int
        summary["total"]         # Decimal (MRP total)
        summary["discount"]      # Decimal (offer discount)
        summary["sub_total"]     # Decimal (after offer discount)
        summary["shipping_fee"]  # Decimal
        summary["tax"]           # Decimal
        summary["grand_total"]   # Decimal
        summary["cart_items"]    # list of cart items (variants are packed)

    DB cost: fetch_cart queries + 2 from pack_variants.
    """
    cart_items = list(fetch_cart(cart))

    # Pack all variants in one shot (2 DB queries)
    variants = [item.product_variant for item in cart_items]
    pack_variants(variants)

    # Single pass over items to compute everything
    total = Decimal("0.00")  # MRP total
    sub_total = Decimal("0.00")  # after-discount total
    discount = Decimal("0.00")  # offer discount
    shipping_fee = Decimal("0.00")

    for item in cart_items:
        v = item.product_variant
        qty = item.quantity

        item_base = v.price * qty
        item_final = v.final_price * qty
        item_disc = v.discount_amount * qty

        # Attach to item for template/view access
        item._total_amount = item_final
        item._total_base = item_base
        item._total_discount = item_disc
        item._item_price = v.final_price

        total += item_base
        sub_total += item_final
        discount += item_disc
        shipping_fee += Decimal(qty * settings.SHIPPING_CHARGE)

    total_amount = sub_total + shipping_fee
    tax = total_amount * Decimal(settings.GST_RATE) / Decimal(100)
    grand_total = total_amount + tax

    return {
        "cart_items": cart_items,
        "items_count": len(cart_items),
        "total": total,
        "discount": discount,
        "sub_total": sub_total,
        "shipping_fee": shipping_fee,
        "total_amount": total_amount,
        "tax": tax,
        "grand_total": grand_total,
    }


def build_cart_summary(cart_items):
    """
    Build the product list for cart display (cart page, offcanvas).
    Expects cart_items from fetch_cart() with variants already packed.
    """
    # Pack all variants
    variants = [item.product_variant for item in cart_items]
    pack_variants(variants)

    products = []
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
                    "image": image.image.url if image else "",
                },
                "allowed_max": min(variant.stock, max_purchase_limit),
                "quantity": item.quantity,
                "total_amount": variant.final_price * item.quantity,
                "total_discount": variant.discount_amount * item.quantity,
            }
        )
    return products


def summary_to_json(summary):
    """Convert summary dict to JSON-safe floats."""
    return {
        "products_count": summary["items_count"],
        "total": float(summary["total"]),
        "discount": float(summary["discount"]),
        "sub_total": float(summary["sub_total"]),
        "shipping_fee": float(summary["shipping_fee"]),
        "total_amount_to_pay": float(summary["total_amount"]),
    }
