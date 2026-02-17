from decimal import Decimal
from django.db import transaction as db_transaction

from users.wallet.models import Wallet, WalletTransaction


class InsufficientBalanceError(Exception):
    pass


class WalletInactiveError(Exception):
    pass


# ────────────────────────────────────────────
# Wallet CRUD
# ────────────────────────────────────────────

def get_or_create_wallet(user):
    """Get existing wallet or create one with zero balance."""
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def can_pay_with_wallet(user, amount):
    """Check if user's wallet has enough balance."""
    wallet = get_or_create_wallet(user)
    return wallet.is_active and wallet.balance >= Decimal(str(amount))


# ────────────────────────────────────────────
# Credit / Debit
# ────────────────────────────────────────────

def credit_wallet(user, amount, transaction_obj=None):
    """
    Add funds to user's wallet.
    Creates a WalletTransaction linked to the universal Transaction.
    """
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError("Credit amount must be positive.")

    with db_transaction.atomic():
        wallet = get_or_create_wallet(user)
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        if not wallet.is_active:
            raise WalletInactiveError("Wallet is inactive.")

        balance_before = wallet.balance
        wallet.balance += amount
        wallet.save(update_fields=["balance", "updated_at"])

        wt = WalletTransaction.objects.create(
            transaction=transaction_obj,
            wallet=wallet,
            label="CREDIT",
            balance_before=balance_before,
            balance_after=wallet.balance,
        )

    return wt


def debit_wallet(user, amount, transaction_obj=None):
    """
    Deduct funds from user's wallet.
    Creates a WalletTransaction linked to the universal Transaction.
    """
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError("Debit amount must be positive.")

    with db_transaction.atomic():
        wallet = get_or_create_wallet(user)
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        if not wallet.is_active:
            raise WalletInactiveError("Wallet is inactive.")

        if wallet.balance < amount:
            raise InsufficientBalanceError(
                f"Insufficient wallet balance. Available: ₹{wallet.balance}, Required: ₹{amount}"
            )

        balance_before = wallet.balance
        wallet.balance -= amount
        wallet.save(update_fields=["balance", "updated_at"])

        wt = WalletTransaction.objects.create(
            transaction=transaction_obj,
            wallet=wallet,
            label="DEBIT",
            balance_before=balance_before,
            balance_after=wallet.balance,
        )

    return wt
