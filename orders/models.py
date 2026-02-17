from decimal import Decimal
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# ======================================================
# STATUS TIMELINE (GENERIC – Order & OrderItem)
# ======================================================


class StatusTimeline(models.Model):

    # ---------------- ORDER STATUSES ----------------
    ORDER_STATUSES = (
        ("PLACED", "Pending Review"),
        ("CONFIRMED", "Order Confirmed"),
        ("SHIPPED", "Dispatched"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    )

    # ---------------- ORDER ITEM STATUSES ----------------
    ORDER_ITEM_STATUSES = (
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("PACKING", "Packing"),
        ("READY", "Ready to Dispatch"),
        ("SHIPPED", "Shipped"),
        ("IN_TRANSIT", "In Transit"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("FAILED", "Delivery Failed"),
        ("RTS", "Returned to Sender"),
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
        max_length=50, editable=False, db_index=True, unique=True
    )

    billing_address = models.JSONField()
    shipping_address = models.JSONField()

    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    payment = models.OneToOneField(
        "payments.Transaction",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order",
    )

    status = GenericRelation(
        StatusTimeline,
        related_query_name="orders",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    # ---------------- ORDER NUMBER ----------------
    def generate_order_number(self):
        while True:
            order_number = f"ORD-{uuid.uuid4().hex[-8:].upper()}"
            if not Order.objects.filter(order_number=order_number).exists():
                return order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    # ---------------- HELPERS ----------------

    @property
    def current_status(self):
        return self.status.first()

    @property
    def can_generate_invoice(self):
        return self.current_status.status in (
            "CONFIRMED",
            "SHIPPED",
            "OUT_FOR_DELIVERY",
            "DELIVERED",
        )

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
    transactions = GenericRelation(
        "payments.Transaction",
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

    @property
    def can_return(self):
        """
        Item is returnable only if:
        1. Current status is DELIVERED
        2. Within 7 days of the delivery date
        3. No pending (REQUESTED/APPROVED) return already exists
        """
        current = self.current_status
        if not current or current.status != "DELIVERED":
            return False

        if self.returns.filter(status__in=["REQUESTED", "APPROVED","REJECTED"]).exists():
            return False

        delivered_entry = self.status.filter(status="DELIVERED").first()
        if not delivered_entry:
            return False

        days_since = (timezone.now() - delivered_entry.created_at).days
        return days_since <= 7


    def __str__(self):
        return f"OrderItem #{self.id} ({self.product_variant})"


# ======================================================
# RETURN MODEL
# ======================================================


class Return(models.Model):

    REASON_CODES = (
        ("CHANGED_MIND", "Changed my mind"),
        ("WRONG_ITEM_ORDERED", "Ordered wrong item"),
        ("FOUND_BETTER_PRICE", "Found better price"),
        ("DELIVERY_DELAY", "Delivery delay"),
        ("DAMAGED_ITEM", "Item damaged"),
        ("DEFECTIVE_ITEM", "Item defective"),
        ("WRONG_ITEM_RECEIVED", "Wrong item received"),
        ("SIZE_FIT_ISSUE", "Size/Fit issue"),
        ("QUALITY_NOT_AS_EXPECTED", "Quality not as expected"),
        ("OTHER", "Other"),
    )

    return_number = models.CharField(
        max_length=50,
        editable=False,
        unique=True,
        db_index=True,
    )

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="returns",
    )

    STATUS_CHOICES = (
        ("REQUESTED", "Requested"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("COMPLETED", "Completed"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="REQUESTED",
    )
    reason_code = models.CharField(max_length=40, choices=REASON_CODES)
    comment = models.TextField(blank=True, null=True)

    admin_note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    transactions = GenericRelation(
        "payments.Transaction",
        related_query_name="returns",
    )

    def generate_return_number(self):
        while True:
            return_number = f"RE-{uuid.uuid4().hex[-6:].upper()}"
            if not Return.objects.filter(return_number=return_number).exists():
                return return_number

    def save(self, *args, **kwargs):
        if not self.return_number:
            self.return_number = self.generate_return_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Return #{self.return_number} - {self.order_item_id} - {self.reason_code}"
        )


# ======================================================
# RETURN IMAGE MODEL
# ======================================================


class ReturnImage(models.Model):

    return_request = models.ForeignKey(
        Return,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="order_return/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"Image for {self.return_request.return_number}"
