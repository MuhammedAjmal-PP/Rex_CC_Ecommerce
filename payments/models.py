import uuid
from decimal import Decimal
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


# ======================================================
# TRANSACTION MODEL
# ======================================================


class Transaction(models.Model):
    """
    Universal financial ledger entry.
    Every money movement creates one of these — GenericFK links
    to the source object (Order, OrderItem, Return, Wallet, etc.).
    """

    # ── What happened ──────────────────────────
    TRANSACTION_TYPES = (
        ("ORDER_PAYMENT", "Order Payment"),
        ("CANCELLATION_REFUND", "Cancellation Refund"),
        ("RETURN_REFUND", "Return Refund"),
        ("WALLET_CREDIT", "Wallet Credit"),
        ("WALLET_DEBIT", "Wallet Debit"),
    )

    # ── How (payment method) ───────────────────
    PAYMENT_METHODS = (
        ("COD", "Cash on Delivery"),
        ("WALLET", "Wallet"),
        ("RAZORPAY", "Razorpay"),
    )

    # ── Status ─────────────────────────────────
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    )

    # ── Core Fields ────────────────────────────
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    # ── GenericFK → any source object ──────────
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

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
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["transaction_type", "status"]),
        ]

    def __str__(self):
        return (
            f"{self.get_transaction_type_display()} "
            f"₹{self.amount} ({self.get_status_display()}) "
            f"— {self.get_payment_method_display()}"
        )
