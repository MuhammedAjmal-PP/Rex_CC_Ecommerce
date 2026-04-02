from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from django.db import transaction as db_transaction
from payments.models import Transaction
from users.wallet.service import credit_wallet

# ────────────────────────────────────────────
# Create Transaction Record
# ────────────────────────────────────────────


def create_transaction(
    user,
    txn_type,
    method,
    amount,
    status="PENDING",
    content_object=None,
    note="",
):
    """
    Create a universal Transaction record.
    Optionally links to a source object via GenericFK.
    """
    ct = None
    obj_id = None
    if content_object is not None:
        ct = ContentType.objects.get_for_model(content_object)
        obj_id = content_object.pk

    return Transaction.objects.create(
        user=user,
        transaction_type=txn_type,
        payment_method=method,
        amount=Decimal(str(amount)),
        status=status,
        content_type=ct,
        object_id=obj_id,
        note=note,
    )


def update_transaction(*, order, amount, note=""):
    """
    Update a pending transaction (usually COD)
    when a partial cancellation occurs.
    """
    from orders.utils import get_payment_transaction

    txn = get_payment_transaction(order)
    if txn and txn.status == "PENDING":
        new_amount = txn.amount - amount

        if new_amount <= 0:
            txn.status = "CANCELLED"
            txn.note = f"{txn.note} | Order cancelled"
        else:
            txn.amount = new_amount
            txn.note = f"{txn.note} | {note}"

        txn.save(update_fields=["amount", "note", "updated_at", "status"])

    return txn


# ────────────────────────────────────────────
# Refund Operations (admin-controlled)
# ────────────────────────────────────────────


def initiate_refund(order, user, amount, txn_type, content_object=None, note=""):
    """
    Create a PENDING refund Transaction.
    Called on cancellation / return completion.
    Stays PENDING until admin approves.
    """
    return create_transaction(
        user=user,
        txn_type=txn_type,
        method="WALLET",
        amount=amount,
        status="PENDING",
        content_object=content_object or order,
        note=note,
    )


def complete_refund(transaction, wallet_reason="WALLET_CREDIT"):
    """
    Admin approves a refund:
      1. Mark Transaction → COMPLETED
      2. Credit the user's wallet
    """
    if transaction.status != "PENDING":
        raise ValueError(
            f"Cannot complete refund — current status is {transaction.status}"
        )

    with db_transaction.atomic():
        transaction.status = "COMPLETED"
        transaction.save(update_fields=["status", "updated_at"])

        credit_wallet(
            user=transaction.user,
            amount=transaction.amount,
            transaction_obj=transaction,
        )

    return transaction


# ────────────────────────────────────────────
# Status Helpers
# ────────────────────────────────────────────


def fail_transaction(transaction, note=""):
    """Mark a PENDING transaction as FAILED."""
    if transaction.status != "PENDING":
        raise ValueError(f"Cannot fail — current status is {transaction.status}")
    transaction.status = "FAILED"
    if note:
        transaction.note = note
    transaction.save(update_fields=["status", "note", "updated_at"])
    return transaction


# Alias for backward compatibility
fail_refund = fail_transaction
