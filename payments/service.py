from decimal import Decimal
from django.db import transaction as db_transaction

from payments.models import PaymentTransaction
from users.wallet.service import credit_wallet


# ────────────────────────────────────────────
# Create Payment Records
# ────────────────────────────────────────────

def create_payment(order, user, method, txn_type, amount, status="PENDING", note=""):
    """
    Create a raw PaymentTransaction record.
    Used by checkout (PAYMENT) and refund flows (REFUND).
    """
    return PaymentTransaction.objects.create(
        order=order,
        user=user,
        payment_method=method,
        transaction_type=txn_type,
        amount=Decimal(str(amount)),
        status=status,
        note=note,
    )


# ────────────────────────────────────────────
# Refund Operations (admin-controlled)
# ────────────────────────────────────────────

def initiate_refund(order, user, amount, reason_note=""):
    """
    Create a PENDING refund PaymentTransaction.
    Called when an order is cancelled or a return is completed.
    The refund stays PENDING until admin approves it.
    """
    return create_payment(
        order=order,
        user=user,
        method=order.payment_method,
        txn_type="REFUND",
        amount=amount,
        status="PENDING",
        note=reason_note,
    )


def complete_refund(payment_transaction, wallet_reason="ORDER_REFUND"):
    """
    Admin approves a refund:
      1. Mark PaymentTransaction → COMPLETED
      2. Credit the user's wallet

    Args:
        payment_transaction: The PENDING refund PaymentTransaction
        wallet_reason: Reason code for the WalletTransaction
                       (ORDER_REFUND, RETURN_REFUND, CANCELLATION_REFUND)
    """
    if payment_transaction.status != "PENDING":
        raise ValueError(
            f"Cannot complete refund — current status is {payment_transaction.status}"
        )
    if payment_transaction.transaction_type != "REFUND":
        raise ValueError("This transaction is not a refund.")

    with db_transaction.atomic():
        payment_transaction.status = "COMPLETED"
        payment_transaction.save(update_fields=["status", "updated_at"])

        credit_wallet(
            user=payment_transaction.user,
            amount=payment_transaction.amount,
            reason=wallet_reason,
            payment=payment_transaction,
            description=(
                f"Refund for Order {payment_transaction.order.order_number} — "
                f"₹{payment_transaction.amount}"
            ),
        )

    return payment_transaction


def fail_refund(payment_transaction, note=""):
    """
    Admin rejects a refund — mark PaymentTransaction → FAILED.
    """
    if payment_transaction.status != "PENDING":
        raise ValueError(
            f"Cannot fail refund — current status is {payment_transaction.status}"
        )

    payment_transaction.status = "FAILED"
    if note:
        payment_transaction.note = note
    payment_transaction.save(update_fields=["status", "note", "updated_at"])
    return payment_transaction


# ────────────────────────────────────────────
# Payment Status Updates
# ────────────────────────────────────────────

def complete_payment(payment_transaction):
    """Mark a PENDING payment as COMPLETED."""
    if payment_transaction.status != "PENDING":
        raise ValueError(
            f"Cannot complete — current status is {payment_transaction.status}"
        )
    payment_transaction.status = "COMPLETED"
    payment_transaction.save(update_fields=["status", "updated_at"])
    return payment_transaction


def fail_payment(payment_transaction, note=""):
    """Mark a PENDING payment as FAILED."""
    if payment_transaction.status != "PENDING":
        raise ValueError(
            f"Cannot fail — current status is {payment_transaction.status}"
        )
    payment_transaction.status = "FAILED"
    if note:
        payment_transaction.note = note
    payment_transaction.save(update_fields=["status", "note", "updated_at"])
    return payment_transaction
