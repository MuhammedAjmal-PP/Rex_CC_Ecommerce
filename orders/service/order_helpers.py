"""
Order placement helpers — business logic used by place_order and razorpay views.
"""
from decimal import Decimal
from catalog.models import ProductVariant
from catalog.service import update_stock
from orders.models import OrderItem
from orders.service import InsufficientStockError


def build_cart_snapshot(cart_items, packed_prices, locked_variants):
    """
    Build a JSON-serialisable snapshot of the cart.
    Saved on the Order so items can be created later (after Razorpay payment).

    Returns a list like:
    [
        {"variant_id": 42, "quantity": 2, "price": "999.00", "original_price": "1299.00"},
        ...
    ]
    """
    snapshot = []
    for item in cart_items:
        vid = item.product_variant_id
        locked = locked_variants[vid]
        snapshot.append({
            "variant_id": vid,
            "quantity": item.quantity,
            "price": str(packed_prices.get(vid, locked.price)),
            "original_price": str(locked.price),
        })
    return snapshot


def create_items_from_snapshot(order, snapshot, actor):
    """
    Create OrderItems and deduct stock from a saved cart_snapshot.
    Used by the Razorpay callback after payment is verified.

    Steps:
      1. Lock variants (SELECT FOR UPDATE)
      2. Validate stock is still available
      3. Create OrderItem records
      4. Deduct stock for each item
    """
    # 1. Lock variants to prevent race conditions
    variant_ids = sorted({entry["variant_id"] for entry in snapshot})
    locked_variants = {
        v.id: v
        for v in ProductVariant.objects.select_for_update().filter(id__in=variant_ids)
    }

    # 2. Check stock availability
    for entry in snapshot:
        variant = locked_variants.get(entry["variant_id"])
        if not variant or entry["quantity"] > variant.stock:
            raise InsufficientStockError(
                f"Insufficient stock for {variant or 'unknown variant'}."
            )

    # 3 & 4. Create items and deduct stock
    for entry in snapshot:
        variant = locked_variants[entry["variant_id"]]

        order_item = OrderItem.objects.create(
            order=order,
            product_variant=variant,
            quantity=entry["quantity"],
            price=Decimal(entry["price"]),
            original_price=Decimal(entry["original_price"]),
        )

        update_stock(
            product_variant=variant,
            change=-entry["quantity"],
            reason="ORDER_PLACED",
            actor=actor,
            reference_object=order_item,
            note=f"Order {order.order_number} placed",
        )
