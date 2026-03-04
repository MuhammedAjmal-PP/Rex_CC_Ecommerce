from django.contrib import admin

from orders.models import Order, OrderItem, Return, ReturnImage


# ======================================================
# ORDER ITEM INLINE
# ======================================================


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("total_price",)
    fields = (
        "product_variant",
        "quantity",
        "price",
        "status",
    )


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

    readonly_fields = ("order_number", "payment", "created_at", "status_updated_at")

    inlines = [
        OrderItemInline,
    ]


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
        "total_price",
    )
    list_filter = ("status", "order__created_at")
    search_fields = ("order__order_number", "product_variant__product__name")


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
