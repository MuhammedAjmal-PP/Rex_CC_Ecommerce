from django.contrib import admin
from django.utils.html import mark_safe
from orders.models import Order, OrderItem, Return, ReturnImage


# ======================================================
# ORDER ITEM INLINE
# ======================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("get_total_price",)
    fields = (
        "product_variant",
        "quantity",
        "price",
        "status",
        "get_total_price",
    )

    @admin.display(description="Total Price")
    def get_total_price(self, obj):
        if obj and obj.price is not None and obj.quantity is not None:
            return f"₹{obj.price * obj.quantity}"
        return "-"


# ======================================================
# ORDER ADMIN
# ======================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "grand_total",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "user__email", "user__phone")
    ordering = ("-created_at",)
    readonly_fields = (
        "order_number",
        "created_at",
        "status_updated_at",
        "payment_summary",
    )
    inlines = [OrderItemInline]

    @admin.display(description="Payment Transactions")
    def payment_summary(self, obj):
        if not obj or not obj.pk:
            return "No transactions"

        transactions = obj.payment.all()
        if not transactions.exists():
            return "No transactions"

        rows = "".join(
            f"<tr>"
            f"<td style='padding:4px 8px;border:1px solid #ccc'>{txn.transaction_id}</td>"
            f"<td style='padding:4px 8px;border:1px solid #ccc'>{txn.get_transaction_type_display()}</td>"
            f"<td style='padding:4px 8px;border:1px solid #ccc'>{txn.get_payment_method_display()}</td>"
            f"<td style='padding:4px 8px;border:1px solid #ccc'>₹{txn.amount}</td>"
            f"<td style='padding:4px 8px;border:1px solid #ccc'>{txn.get_status_display()}</td>"
            f"</tr>"
            for txn in transactions
        )

        return mark_safe(
            "<table style='border-collapse:collapse;font-size:13px;'>"
            "<thead><tr>"
            "<th style='padding:4px 8px;border:1px solid #ccc'>ID</th>"
            "<th style='padding:4px 8px;border:1px solid #ccc'>Type</th>"
            "<th style='padding:4px 8px;border:1px solid #ccc'>Method</th>"
            "<th style='padding:4px 8px;border:1px solid #ccc'>Amount</th>"
            "<th style='padding:4px 8px;border:1px solid #ccc'>Status</th>"
            "</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )


# ======================================================
# ORDER ITEM ADMIN
# ======================================================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_variant",
        "quantity",
        "price",
        "status",
        "get_total_price",
    )
    list_filter = ("status", "order__created_at")
    search_fields = ("order__order_number", "product_variant__product__name")
    readonly_fields = ("get_total_price",)

    @admin.display(description="Total Price")
    def get_total_price(self, obj):
        if obj and obj.price is not None and obj.quantity is not None:
            return f"₹{obj.price * obj.quantity}"
        return "-"


# ======================================================
# RETURN ADMIN
# ======================================================
class ReturnImageInline(admin.TabularInline):
    model = ReturnImage
    extra = 0
    readonly_fields = ("image", "uploaded_at")


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = (
        "return_number",
        "order_item",
        "status",
        "reason_code",
        "created_at",
    )
    list_filter = ("status", "reason_code")
    search_fields = ("return_number", "order_item__order__order_number")
    ordering = ("-created_at",)
    readonly_fields = ("return_number", "created_at")
    inlines = [ReturnImageInline]
