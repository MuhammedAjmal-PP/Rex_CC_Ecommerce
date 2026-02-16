from decimal import Decimal
from django.db import transaction as db_transaction

from users.wallet.models import Wallet, WalletTransaction


class InsufficientBalanceError(Exception):
    """Raised when wallet balance is not sufficient for a debit."""


class WalletInactiveError(Exception):
    """Raised when wallet is frozen/inactive."""


# ────────────────────────────────────────────
# Wallet Access
# ────────────────────────────────────────────

def get_or_create_wallet(user):
    """Lazily create a wallet for the user if it doesn't exist."""
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def can_pay_with_wallet(user, amount):
    """Check if the user's wallet has enough balance."""
    try:
        wallet = Wallet.objects.get(user=user)
        return wallet.is_active and wallet.balance >= Decimal(str(amount))
    except Wallet.DoesNotExist:
        return False


# ────────────────────────────────────────────
# Credit / Debit (atomic + select_for_update)
# ────────────────────────────────────────────

def credit_wallet(user, amount, reason, payment=None, description=""):
    """
    Add funds to the user's wallet.
    Creates a WalletTransaction with type=CREDIT.
    """
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError("Credit amount must be positive.")

    with db_transaction.atomic():
        wallet = get_or_create_wallet(user)
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        if not wallet.is_active:
            raise WalletInactiveError("Wallet is inactive.")

        wallet.balance += amount
        wallet.save(update_fields=["balance", "updated_at"])

        txn = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type="CREDIT",
            amount=amount,
            balance_after=wallet.balance,
            reason=reason,
            description=description,
            payment=payment,
        )
    return txn


def debit_wallet(user, amount, reason, payment=None, description=""):
    """
    Deduct funds from the user's wallet.
    Creates a WalletTransaction with type=DEBIT.
    Raises InsufficientBalanceError if balance < amount.
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

        wallet.balance -= amount
        wallet.save(update_fields=["balance", "updated_at"])

        txn = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type="DEBIT",
            amount=amount,
            balance_after=wallet.balance,
            reason=reason,
            description=description,
            payment=payment,
        )
    return txn
