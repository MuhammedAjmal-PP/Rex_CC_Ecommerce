from django.utils import timezone


class InvalidTransitionError(Exception):
    """Raised when a status transition is not allowed."""


ORDER_ALLOWED_TRANSITIONS = {
    "PLACED": {"CONFIRMED", "CANCELLED", "FAILED", "STOCK_UNAVAILABLE"},
    "CONFIRMED": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"OUT_FOR_DELIVERY"},
    "OUT_FOR_DELIVERY": {"DELIVERED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
    "FAILED": {"PLACED", "EXPIRED"},
    "EXPIRED": set(),
    "STOCK_UNAVAILABLE": set(),
}

ORDER_ITEM_ALLOWED_TRANSITIONS = {
    "PENDING": {"CONFIRMED", "CANCELLED", "FAILED"},
    "CONFIRMED": {"PACKING", "CANCELLED"},
    "PACKING": {"READY", "CANCELLED"},
    "READY": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"IN_TRANSIT"},
    "IN_TRANSIT": {"OUT_FOR_DELIVERY"},
    "OUT_FOR_DELIVERY": {"DELIVERED", "FAILED"},
    "FAILED": {"OUT_FOR_DELIVERY", "RTS", "CANCELLED", "PENDING"},
    "DELIVERED": {"RETURN_REQUESTED"},
    "RETURN_REQUESTED": {"RETURNED", "DELIVERED"},
    "RETURNED": set(),
    "RTS": set(),
    "CANCELLED": set(),
}

# Admin-only transitions: stops at DELIVERED (no RETURN_REQUESTED)
ADMIN_ITEM_ALLOWED_TRANSITIONS = {
    "PENDING": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"PACKING", "CANCELLED"},
    "PACKING": {"READY", "CANCELLED"},
    "READY": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"IN_TRANSIT"},
    "IN_TRANSIT": {"OUT_FOR_DELIVERY"},
    "OUT_FOR_DELIVERY": {"DELIVERED", "FAILED"},
    "FAILED": {"OUT_FOR_DELIVERY", "RTS", "CANCELLED"},
    "DELIVERED": set(),
    "RETURN_REQUESTED": set(),
    "RETURNED": set(),
    "RTS": set(),
    "CANCELLED": set(),
}

# Ordered item status progression (happy path)
ITEM_STATUS_CHAIN = [
    "PENDING",
    "CONFIRMED",
    "PACKING",
    "READY",
    "SHIPPED",
    "IN_TRANSIT",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
]

# Order status → target item status for cascade
ORDER_TO_ITEM_TARGET = {
    "CONFIRMED": "CONFIRMED",
    "SHIPPED": "SHIPPED",
    "OUT_FOR_DELIVERY": "OUT_FOR_DELIVERY",
    "DELIVERED": "DELIVERED",
    "CANCELLED": "CANCELLED",
    "FAILED": "FAILED",
}


def can_transition(*, model_type, from_status, to_status):
    """Check if transitioning from from_status to to_status is allowed."""
    if model_type == "order":
        transitions = ORDER_ALLOWED_TRANSITIONS
    elif model_type == "orderitem":
        transitions = ORDER_ITEM_ALLOWED_TRANSITIONS
    else:
        return False

    return to_status in transitions.get(from_status, set())


def _change_status(*, obj, model_type, to_status):
    from_status = obj.status

    if not can_transition(
        model_type=model_type,
        from_status=from_status,
        to_status=to_status,
    ):
        raise InvalidTransitionError(
            f"Invalid {model_type} transition: {from_status or 'NONE'} -> {to_status}"
        )

    obj.status = to_status
    obj.status_updated_at = timezone.now()
    obj.save(update_fields=["status", "status_updated_at"])
    return obj


# ────────────────────────────────────────────
# Item → Order sync (called after item change)
# ────────────────────────────────────────────
def _sync_order_status(order, *, items=None):
    """
    Derive the order-level status from all its items.
    Accepts a pre-loaded items list to avoid N+1 queries (fix #4).
    Called automatically after every item status change.
    """
    if items is None:
        items = list(order.items.all())
    if not items:
        return

    item_statuses = {item.status for item in items}
    current_order_status = order.status

    # Post-delivery statuses (return flow): treated as "delivered" for order sync
    _POST_DELIVERY = {"DELIVERED", "RETURN_REQUESTED", "RETURNED"}

    # Rule 1: ALL items cancelled → cancel the order
    if item_statuses == {"CANCELLED"}:
        target = "CANCELLED"
    # Rule 1b: ALL items FAILED or some FAILED + rest CANCELLED → fail the order (fix #20)
    elif item_statuses <= {"FAILED", "CANCELLED"} and "FAILED" in item_statuses:
        target = "FAILED"
    # Rule 2: ALL items delivered/returned/cancelled (at least one post-delivery) → deliver
    elif (
        item_statuses <= (_POST_DELIVERY | {"CANCELLED"})
        and item_statuses & _POST_DELIVERY
    ):
        target = "DELIVERED"
    # Rule 3: Any item out-for-delivery (rest delivered/cancelled) → out for delivery
    elif (
        item_statuses <= ({"OUT_FOR_DELIVERY"} | _POST_DELIVERY | {"CANCELLED"})
        and "OUT_FOR_DELIVERY" in item_statuses
    ):
        target = "OUT_FOR_DELIVERY"
    # Rule 4: Any item shipped/in-transit (rest further along or cancelled) → shipped
    elif item_statuses & {"SHIPPED", "IN_TRANSIT"}:
        target = "SHIPPED"
    # Rule 5: All items confirmed+ (none pending) → confirmed
    elif "PENDING" not in item_statuses and item_statuses & {
        "CONFIRMED",
        "PACKING",
        "READY",
    }:
        target = "CONFIRMED"
    else:
        return  # No auto-change needed

    # Only transition if it's actually different and valid
    if target != current_order_status and can_transition(
        model_type="order",
        from_status=current_order_status,
        to_status=target,
    ):
        _change_status(obj=order, model_type="order", to_status=target)


# ────────────────────────────────────────────
# Order → Items cascade (called after order change)
# ────────────────────────────────────────────
def _cascade_order_to_items(order, to_status):
    """
    Push order-level status down to eligible items.
    Items walk through every intermediate status in the chain.
    CANCELLED/FAILED are direct jumps (no walk needed).
    """
    target_item_status = ORDER_TO_ITEM_TARGET.get(to_status)
    if not target_item_status:
        return

    for item in order.items.all():
        item_status = item.status
        if item_status == "CANCELLED":
            continue

        # CANCELLED / FAILED: direct jump (no walk needed)
        if target_item_status in ("CANCELLED", "FAILED"):
            if can_transition(
                model_type="orderitem",
                from_status=item_status,
                to_status=target_item_status,
            ):
                _change_status(
                    obj=item,
                    model_type="orderitem",
                    to_status=target_item_status,
                )
            continue

        # Progressive walk: find current and target positions in chain
        if (
            item_status not in ITEM_STATUS_CHAIN
            or target_item_status not in ITEM_STATUS_CHAIN
        ):
            continue

        current_idx = ITEM_STATUS_CHAIN.index(item_status)
        target_idx = ITEM_STATUS_CHAIN.index(target_item_status)

        # Only move forward, skip if already at or past target
        if current_idx >= target_idx:
            continue

        # Walk through each intermediate status
        for step_idx in range(current_idx + 1, target_idx + 1):
            step_status = ITEM_STATUS_CHAIN[step_idx]
            _change_status(
                obj=item,
                model_type="orderitem",
                to_status=step_status,
            )


# ────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────
def change_order_status(*, order, to_status):
    result = _change_status(obj=order, model_type="order", to_status=to_status)

    # Auto-update COD payment status to PAID upon delivery
    from orders.utils import get_payment_transaction
    payment = get_payment_transaction(order)
    if to_status == "DELIVERED" and payment:
        if payment.payment_method == "COD" and payment.status == "PENDING":
            payment.status = "PAID"
            payment.save(update_fields=["status", "updated_at"])

    _cascade_order_to_items(order, to_status)
    return result


def change_order_item_status(*, order_item, to_status):
    result = _change_status(obj=order_item, model_type="orderitem", to_status=to_status)
    # Load all sibling items once and pass into sync to avoid N+1 (fix #4)
    all_items = list(order_item.order.items.all())
    _sync_order_status(order_item.order, items=all_items)
    return result
