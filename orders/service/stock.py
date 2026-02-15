from catalog.models import ProductVariant


class InsufficientStockError(Exception):
    """Raised when requested quantity is greater than available stock."""


def validate_stock(*, cart_items, stock_lookup):
    for item in cart_items:
        variant = stock_lookup[item.product_variant_id]
        if item.quantity > variant.stock:
            raise InsufficientStockError(f"Insufficient stock for {variant}.")


def build_unlocked_stock_lookup(*, cart_items):
    return {item.product_variant_id: item.product_variant for item in cart_items}


def lock_variants_for_update(*, cart_items):
    variant_ids = sorted({item.product_variant_id for item in cart_items})
    return {
        variant.id: variant
        for variant in ProductVariant.objects.select_for_update().filter(
            id__in=variant_ids
        )
    }
