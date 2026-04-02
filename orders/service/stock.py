from catalog.models import ProductVariant


class InsufficientStockError(Exception):
    """Raised when requested quantity is greater than available stock."""


def validate_stock(*, items, stock_lookup):
    for item in items:
        variant = stock_lookup[item.product_variant_id]
        if item.quantity > variant.stock:
            raise InsufficientStockError(f"Insufficient stock for {variant}.")


def validate_snapshot_stock(snapshot):
    """
    Lock variant rows and validate stock from a cart_snapshot (list of dicts).
    Must be called inside transaction.atomic().

    Returns:
        dict mapping variant_id → locked ProductVariant (for reuse by caller).

    Raises:
        InsufficientStockError if any variant lacks stock.
    """
    variant_ids = sorted({entry["variant_id"] for entry in snapshot})
    locked_variants = {
        v.id: v
        for v in ProductVariant.objects.select_for_update().filter(id__in=variant_ids)
    }
    for entry in snapshot:
        variant = locked_variants.get(entry["variant_id"])
        if not variant or entry["quantity"] > variant.stock:
            raise InsufficientStockError(
                f"Insufficient stock for {variant or 'unknown variant'}."
            )
    return locked_variants


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
