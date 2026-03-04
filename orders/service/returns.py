from orders.models import Return
from orders.utils import can_return_item


class ReturnNotEligibleError(Exception):
    """Raised when item is not eligible for return."""


class DuplicateReturnError(Exception):
    """Raised when a return request already exists."""


def validate_return_eligibility(order_item):
    """
    Check if the order item can be returned.
    Raises distinct exceptions for UI messaging.
    """
    # Must be DELIVERED
    if order_item.status != "DELIVERED":
        raise ReturnNotEligibleError("This item is not eligible for return.")

    # No active/resolved return already exists
    try:
        existing = order_item.return_request
        if existing.status in ("REQUESTED", "APPROVED", "REJECTED"):
            raise DuplicateReturnError("A return request already exists for this item.")
    except Return.DoesNotExist:
        pass

    # Must be within 7-day return window
    if not can_return_item(order_item):
        raise ReturnNotEligibleError(
            "The 7-day return window has expired for this item."
        )

