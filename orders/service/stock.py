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


def restore_order_stock(order, actor):
    """
    Restore stock for all items in a failed order.
    Called when Razorpay payment fails or signature verification fails.
    """
    items = order.items.select_related("product_variant").all()
    for item in items:
        if item.product_variant:
            update_stock(
                product_variant=item.product_variant,
                change=+item.quantity,
                reason="PAYMENT_FAILED",
                actor=actor,
                reference_object=item,
                note=f"Stock restored — payment failed for order {order.order_number}",
            )
