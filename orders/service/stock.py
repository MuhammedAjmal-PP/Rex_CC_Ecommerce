from catalog.models import ProductVariant
from catalog.service import update_stock


class InsufficientStockError(Exception):
    """Raised when requested quantity is greater than available stock."""


def validate_stock(*, items, stock_lookup):
    for item in items:
        variant = stock_lookup[item.product_variant_id]
        if item.quantity > variant.stock:
            raise InsufficientStockError(f"Insufficient stock for {variant}.")


def build_unlocked_stock_lookup(*, items):
    return {item.product_variant_id: item.product_variant for item in items}


def lock_variants_for_update(*, items):
    variant_ids = sorted({item.product_variant_id for item in items})
    return {
        variant.id: variant
        for variant in ProductVariant.objects.select_for_update().filter(
            id__in=variant_ids
        )
    }

