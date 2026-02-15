from orders.service.status import get_current_status

RETURNABLE_STATUSES = {"DELIVERED"}


class ReturnNotEligibleError(Exception):
    """Raised when item is not eligible for return."""


class DuplicateReturnError(Exception):
    """Raised when a return request already exists."""


def validate_return_eligibility(order_item):
    """
    Check if the order item can be returned.
    Raises ReturnNotEligibleError or DuplicateReturnError.
    """
    item_status = get_current_status(order_item)

    if item_status not in RETURNABLE_STATUSES:
        raise ReturnNotEligibleError("This item is not eligible for return.")

    if order_item.returns.filter(status__in=["REQUESTED", "APPROVED"]).exists():
        raise DuplicateReturnError("A return request already exists for this item.")

