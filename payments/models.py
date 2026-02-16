import uuid
from decimal import Decimal
from django.db import models


# ======================================================
# PAYMENT TRANSACTION MODEL
# ======================================================


class PaymentTransaction(models.Model):
    """
    Raw-level payment record.
    Every financial event (order payment, refund) creates one of these.
    Future Razorpay integration will populate gateway_* fields.
    """

    # ── Payment Methods ────────────────────────
    PAYMENT_METHODS = (
        ("COD", "Cash on Delivery"),
        ("WALLET", "Wallet"),
        ("RAZORPAY", "Razorpay"),  # future
    )

    # ── Transaction Types ──────────────────────
    TRANSACTION_TYPES = (
        ("PAYMENT", "Payment"),
        ("REFUND", "Refund"),
    )

    # ── Statuses ───────────────────────────────
    STATUS_CHOICES = (
        ("PENDING", "Pending"),  # awaiting admin approval (refunds)
        ("COMPLETED", "Completed"),  # money moved successfully
        ("FAILED", "Failed"),  # payment/refund failed or rejected
    )

    # ── Core Fields ────────────────────────────
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    # ── Razorpay Gateway Fields (future) ───────
    gateway_order_id = models.CharField(max_length=100, blank=True, default="")
    gateway_payment_id = models.CharField(max_length=100, blank=True, default="")
    gateway_signature = models.CharField(max_length=200, blank=True, default="")

    # ── Metadata ───────────────────────────────
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.get_transaction_type_display()} "
            f"₹{self.amount} ({self.get_status_display()}) "
            f"— {self.get_payment_method_display()}"
        )
