from decimal import Decimal
import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation


# ======================================================
# ORDER MODEL
# ======================================================


class Order(models.Model):

    ORDER_STATUS_CHOICES = [
        ("PLACED", "Pending Review"),
        ("CONFIRMED", "Order Confirmed"),
        ("SHIPPED", "Dispatched"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
        ("FAILED", "Payment Failed"),
    ]

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
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    # ── Coupon ────────────────────
    coupon = models.ForeignKey(
        "coupons.Coupon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    coupon_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Coupon discount amount applied at order time",
    )

    payment = GenericRelation(
        "payments.Transaction",
        related_query_name="orders",
    )

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="PLACED",
        db_index=True,
    )
    status_updated_at = models.DateTimeField(auto_now=True)

    cart_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Cart data saved at order time, used to create items after Razorpay payment",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def generate_order_number(self):
        for _ in range(20):
            order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
            if not Order.objects.filter(order_number=order_number).exists():
                return order_number
        raise RuntimeError("Could not generate a unique order number after 20 retries.")

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number}"


# ======================================================
# ORDER ITEM MODEL
# ======================================================


class OrderItem(models.Model):

    ITEM_STATUS_CHOICES = [
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
    ]

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
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="MRP / list price at the time the order was placed (before any offer discount)",
    )

    status = models.CharField(
        max_length=20,
        choices=ITEM_STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )
    status_updated_at = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    transactions = GenericRelation(
        "payments.Transaction",
        related_query_name="order_items",
    )

    @property
    def total_price(self):
        return self.price * self.quantity

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

    order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="return_request",
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
