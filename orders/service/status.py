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
    "READY": {"SHIPPED"},
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


def change_order_status(*, order, to_status, actor=None, note=""):
    return _change_status(
        obj=order,
        model_type="order",
        to_status=to_status,
        actor=actor,
        note=note,
    )


def change_order_item_status(*, order_item, to_status, actor=None, note=""):
    return _change_status(
        obj=order_item,
        model_type="orderitem",
        to_status=to_status,
        actor=actor,
        note=note,
    )
