from django.contrib import admin
from payments.models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "order",
        "user",
        "payment_method",
        "transaction_type",
        "amount",
        "status",
        "created_at",
    )
    list_filter = ("payment_method", "transaction_type", "status")
    search_fields = (
        "transaction_id",
        "order__order_number",
        "user__email",
    )
    readonly_fields = (
        "transaction_id",
        "order",
        "user",
        "payment_method",
        "transaction_type",
        "amount",
        "gateway_order_id",
        "gateway_payment_id",
        "gateway_signature",
        "created_at",
        "updated_at",
    )
    list_per_page = 25
