import uuid
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
    """Immutable log of every wallet credit/debit."""

    TRANSACTION_TYPES = (
        ("CREDIT", "Credit"),
        ("DEBIT", "Debit"),
    )

    REASON_CHOICES = (
        ("ORDER_REFUND", "Order Refund"),
        ("RETURN_REFUND", "Return Refund"),
        ("CANCELLATION_REFUND", "Cancellation Refund"),
        ("ORDER_PAYMENT", "Order Payment"),
        ("REFERRAL_BONUS", "Referral Bonus"),
    )

    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=40, choices=REASON_CHOICES)
    description = models.TextField(blank=True)

    # Link to the raw payment record (optional)
    payment = models.ForeignKey(
        "payments.PaymentTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transactions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "-created_at"]),
        ]

    def __str__(self):
        sign = "+" if self.transaction_type == "CREDIT" else "-"
        return f"{sign}₹{self.amount} ({self.get_reason_display()}) → ₹{self.balance_after}"
