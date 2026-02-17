from django.contrib import admin
from payments.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "user",
        "transaction_type",
        "payment_method",
        "amount",
        "status",
        "created_at",
    )
    list_filter = ("transaction_type", "payment_method", "status", "created_at")
    search_fields = (
        "transaction_id",
        "user__email",
        "note",
    )
    readonly_fields = (
        "transaction_id",
        "user",
        "transaction_type",
        "payment_method",
        "amount",
        "content_type",
        "object_id",
        "gateway_order_id",
        "gateway_payment_id",
        "gateway_signature",
        "created_at",
        "updated_at",
    )
    list_per_page = 25
