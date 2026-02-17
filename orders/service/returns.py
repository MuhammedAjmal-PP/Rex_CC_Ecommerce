class ReturnNotEligibleError(Exception):
    """Raised when item is not eligible for return."""


class DuplicateReturnError(Exception):
    """Raised when a return request already exists."""


def validate_return_eligibility(order_item):
    """
    Check if the order item can be returned.
    Delegates to OrderItem.can_return for the core logic,
    but raises distinct exceptions for UI messaging.
    """
    current = order_item.current_status

    # Must be DELIVERED
    if not current or current.status != "DELIVERED":
        raise ReturnNotEligibleError("This item is not eligible for return.")

    # No active/resolved return already exists
    if hasattr(order_item, 'return_request') and order_item.return_request.status in ("REQUESTED", "APPROVED", "REJECTED"):
        raise DuplicateReturnError("A return request already exists for this item.")

    # Must be within 7-day return window (uses same logic as can_return)
    if not order_item.can_return:
        raise ReturnNotEligibleError(
            "The 7-day return window has expired for this item."
        )
