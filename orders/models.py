from decimal import Decimal
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

# ======================================================
# STATUS TIMELINE (GENERIC – Order & OrderItem)
# ======================================================


class StatusTimeline(models.Model):

    # ---------------- ORDER STATUSES ----------------
    ORDER_STATUSES = (
        ("PLACED", "Pending Review"),
        ("CONFIRMED", "Order Confirmed"),
        ("INSPECTION", "Quality Check"),
        ("PACKING", "Securing Package"),
        ("READY", "Ready to Dispatch"),
        ("SHIPPED", "Dispatched"),
        ("IN_TRANSIT", "In Transit"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("ON_HOLD", "Action Required"),
        ("FAILED", "Delivery Issue"),
        ("RTS", "Returned to Sender"),
    )

    # ---------------- ORDER ITEM STATUSES ----------------
    ORDER_ITEM_STATUSES = (
        ("PENDING", "Pending"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
        ("RETURN_REQUESTED", "Return Requested"),
        ("RETURNED", "Returned"),
    )

    # Map model → allowed statuses
    CHOICE_MAP = {
        "order": ORDER_STATUSES,
        "orderitem": ORDER_ITEM_STATUSES,
    }

    # ---------------- GENERIC RELATION ----------------
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # NO choices here (validated manually)
    status = models.CharField(max_length=50)

    note = models.TextField(blank=True, null=True)

    # who changed the status (admin / system / courier)
    actor = models.ForeignKey(
        "accounts.CustomUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="status_actions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    # ---------------- VALIDATION ----------------
    @property
    def get_applicable_choices(self):
        return self.CHOICE_MAP.get(self.content_type.model, [])

    def clean(self):
        allowed = [key for key, _ in self.get_applicable_choices]
        if self.status not in allowed:
            raise ValidationError(
                f"Invalid status '{self.status}' for {self.content_type.model}"
            )

        # prevent duplicate consecutive statuses
        last = StatusTimeline.objects.filter(
            content_type=self.content_type,
            object_id=self.object_id,
        ).first()

        if last and last.status == self.status:
            raise ValidationError("Duplicate consecutive status not allowed")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.content_object} → {self.status}"


# ======================================================
# ORDER MODEL
# ======================================================


class Order(models.Model):

    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    order_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        editable=False,
    )

    billing_address = models.JSONField()
    shipping_address = models.JSONField()

    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2)
    grant_total = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(
        max_length=50,
        default="COD",
    )

    status = GenericRelation(
        StatusTimeline,
        related_query_name="orders",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ---------------- ORDER NUMBER ----------------
    def generate_order_number(self):
        while True:
            order_number = f"ORD-{uuid.uuid4().hex[-8:].upper()}"
            if not Order.objects.filter(order_number=order_number).exists():
                return order_number

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)

        if creating and not self.order_number:
            self.order_number = self.generate_order_number()
            super().save(update_fields=["order_number"])

    # ---------------- HELPERS ----------------
    @property
    def current_status(self):
        return self.status.first()

    def __str__(self):
        return f"Order {self.order_number}"


# ======================================================
# ORDER ITEM MODEL
# ======================================================


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
    )

    product_variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    status = GenericRelation(
        StatusTimeline,
        related_query_name="order_items",
    )

    @property
    def total_price(self):
        if self.price is None or self.quantity is None:
            return Decimal("0")
        return self.price * self.quantity

    @property
    def current_status(self):
        return self.status.first()

    def __str__(self):
        return f"OrderItem #{self.id} ({self.product_variant})"
