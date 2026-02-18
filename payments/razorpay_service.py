"""
Razorpay gateway helpers.

- create_razorpay_order()  → calls Razorpay API to create an order
- verify_razorpay_signature() → HMAC-SHA256 verification of callback
"""

import razorpay
from django.conf import settings


def _get_client():
    """Return a configured Razorpay client."""
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_razorpay_order(amount_paise, receipt):
    """
    Create a Razorpay Order.

    Args:
        amount_paise: Amount in paise (₹100 = 10000 paise).
        receipt: A unique receipt string (e.g. order number).

    Returns:
        dict with 'id', 'amount', 'currency', etc.
    """
    client = _get_client()
    return client.order.create(
        {
            "amount": int(amount_paise),
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,  # Auto-capture
        }
    )


def verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verify the payment signature returned by Razorpay checkout.

    Returns:
        True if valid, False otherwise.
    """
    client = _get_client()
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
