class InvalidTransitionError(Exception):
    """Raised when a status transition is not allowed."""


ORDER_ALLOWED_TRANSITIONS = {
    "PLACED": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"OUT_FOR_DELIVERY"},
    "OUT_FOR_DELIVERY": {"DELIVERED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}

ORDER_ITEM_ALLOWED_TRANSITIONS = {
    "PENDING": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"PACKING", "CANCELLED"},
    "PACKING": {"READY", "CANCELLED"},
    "READY": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"IN_TRANSIT"},
    "IN_TRANSIT": {"OUT_FOR_DELIVERY"},
    "OUT_FOR_DELIVERY": {"DELIVERED", "FAILED"},
    "FAILED": {"OUT_FOR_DELIVERY", "RTS", "CANCELLED"},
    "DELIVERED": {"RETURN_REQUESTED"},
    "RETURN_REQUESTED": {"RETURNED"},
    "RETURNED": set(),
    "RTS": set(),
    "CANCELLED": set(),
}

INITIAL_STATUS_BY_MODEL = {
    "order": "PLACED",
    "orderitem": "PENDING",
}

# Mapping: if ALL items reach this item-status → set order to this order-status
_ITEM_TO_ORDER_STATUS = {
    "CANCELLED": "CANCELLED",
    "DELIVERED": "DELIVERED",
}

# When order moves to these statuses, cascade (push) to eligible items
_ORDER_CASCADE_TARGETS = {"CANCELLED", "CONFIRMED"}


def get_current_status(obj):
    current = obj.status.first()
    return current.status if current else None


def can_transition(*, model_type, from_status, to_status):
    if model_type == "order":
        transitions = ORDER_ALLOWED_TRANSITIONS
    elif model_type == "orderitem":
        transitions = ORDER_ITEM_ALLOWED_TRANSITIONS
    else:
        return False

    if from_status is None:
        return to_status == INITIAL_STATUS_BY_MODEL.get(model_type)

    return to_status in transitions.get(from_status, set())


def _change_status(*, obj, model_type, to_status, actor=None, note=""):
    from_status = get_current_status(obj)

    if not can_transition(
        model_type=model_type,
        from_status=from_status,
        to_status=to_status,
    ):
        raise InvalidTransitionError(
            f"Invalid {model_type} transition: {from_status or 'NONE'} -> {to_status}"
        )

    return obj.status.create(
        status=to_status,
        note=note,
        actor=actor,
    )


# ────────────────────────────────────────────
# Item → Order sync (called after item change)
# ────────────────────────────────────────────
def _sync_order_status(order, *, actor=None):
    """
    Derive the order-level status from all its items.
    Called automatically after every item status change.
    """
    items = order.items.all()
    if not items:
        return

    item_statuses = {get_current_status(item) for item in items}

    current_order_status = get_current_status(order)

    # Rule 1: ALL items cancelled → cancel the order
    if item_statuses == {"CANCELLED"}:
        target = "CANCELLED"
    # Rule 2: ALL items delivered (or mix of delivered + cancelled) → deliver
    elif item_statuses <= {"DELIVERED", "CANCELLED"} and "DELIVERED" in item_statuses:
        target = "DELIVERED"
    # Rule 3: Any item out-for-delivery (rest delivered/cancelled) → out for delivery
    elif item_statuses <= {"OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"} and "OUT_FOR_DELIVERY" in item_statuses:
        target = "OUT_FOR_DELIVERY"
    # Rule 4: Any item shipped/in-transit (rest further along or cancelled) → shipped
    elif item_statuses & {"SHIPPED", "IN_TRANSIT"}:
        target = "SHIPPED"
    # Rule 5: All items confirmed+ (none pending) → confirmed
    elif "PENDING" not in item_statuses and item_statuses & {"CONFIRMED", "PACKING", "READY"}:
        target = "CONFIRMED"
    else:
        return  # No auto-change needed

    # Only transition if it's actually different and valid
    if target != current_order_status and can_transition(
        model_type="order",
        from_status=current_order_status,
        to_status=target,
    ):
        _change_status(
            obj=order,
            model_type="order",
            to_status=target,
            actor=actor,
            note=f"Auto-synced: all items reached {target.lower()} state",
        )


# ────────────────────────────────────────────
# Order → Items cascade (called after order change)
# ────────────────────────────────────────────
def _cascade_order_to_items(order, to_status, *, actor=None):
    """
    Push order-level CANCELLED or CONFIRMED down to eligible items.
    Called automatically after an order status change.
    """
    if to_status not in _ORDER_CASCADE_TARGETS:
        return

    for item in order.items.all():
        item_status = get_current_status(item)
        if item_status and can_transition(
            model_type="orderitem",
            from_status=item_status,
            to_status=to_status,
        ):
            _change_status(
                obj=item,
                model_type="orderitem",
                to_status=to_status,
                actor=actor,
                note=f"Auto-cascaded from order status → {to_status}",
            )


# ────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────
def change_order_status(*, order, to_status, actor=None, note=""):
    result = _change_status(
        obj=order,
        model_type="order",
        to_status=to_status,
        actor=actor,
        note=note,
    )
    _cascade_order_to_items(order, to_status, actor=actor)
    return result


def change_order_item_status(*, order_item, to_status, actor=None, note=""):
    result = _change_status(
        obj=order_item,
        model_type="orderitem",
        to_status=to_status,
        actor=actor,
        note=note,
    )
    _sync_order_status(order_item.order, actor=actor)
    return result
