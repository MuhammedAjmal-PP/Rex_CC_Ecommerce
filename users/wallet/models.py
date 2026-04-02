from decimal import Decimal
from django.db import models

# ======================================================
# WALLET MODEL
# ======================================================


class Wallet(models.Model):
    """One wallet per user — holds the current balance."""

    user = models.OneToOneField(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="wallet",
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — ₹{self.balance}"


# ======================================================
# WALLET TRANSACTION MODEL
# ======================================================


class WalletTransaction(models.Model):
    """
    Wallet-specific record linked to a universal Transaction.
    Stores balance snapshots before and after the operation.
    """

    transaction = models.OneToOneField(
        "payments.Transaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transaction",
    )
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="wallet_transactions",
    )
    LABEL_CHOICES = (
        ("CREDIT", "Credit"),
        ("DEBIT", "Debit"),
    )
    label = models.CharField(
        max_length=10,
        choices=LABEL_CHOICES,
        default="CREDIT",  # Default needed for migration, will remove later or set correctly
    )
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "-created_at"]),
        ]

    def __str__(self):
        diff = self.balance_after - self.balance_before
        sign = "+" if diff >= 0 else ""
        return f"{sign}₹{diff} → ₹{self.balance_after}"
