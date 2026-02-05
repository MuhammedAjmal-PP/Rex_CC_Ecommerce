from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from orders.models import Order, OrderItem, StatusTimeline


# ======================================================
# STATUS TIMELINE INLINE (Generic)
# ======================================================
class StatusTimelineInline(GenericTabularInline):
    model = StatusTimeline
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("status", "note", "actor", "created_at")


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
    )


# ======================================================
# ORDER ADMIN
# ======================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "total",
        "payment_method",
        "created_at",
    )
    list_filter = ("payment_method", "created_at")
    search_fields = ("order_number", "user__email", "user__phone")
    ordering = ("-created_at",)

    readonly_fields = ("order_number", "created_at")

    inlines = [
        OrderItemInline,
        StatusTimelineInline,
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
        "total_price",
    )
    list_filter = ("order__created_at",)
    search_fields = ("order__order_number", "product_variant__product__name")

    inlines = [StatusTimelineInline]


# ======================================================
# STATUS TIMELINE ADMIN (Optional but useful)
# ======================================================
@admin.register(StatusTimeline)
class StatusTimelineAdmin(admin.ModelAdmin):
    list_display = (
        "content_object",
        "status",
        "actor",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("status", "note")
    readonly_fields = ("created_at",)
