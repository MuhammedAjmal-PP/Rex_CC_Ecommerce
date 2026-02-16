from django.contrib import admin
from users.wallet.models import Wallet, WalletTransaction


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = (
        "transaction_id",
        "transaction_type",
        "amount",
        "balance_after",
        "reason",
        "description",
        "payment",
        "created_at",
    )
    can_delete = False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("user__email",)
    readonly_fields = ("balance", "created_at", "updated_at")
    inlines = [WalletTransactionInline]


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "wallet",
        "transaction_type",
        "amount",
        "balance_after",
        "reason",
        "created_at",
    )
    list_filter = ("transaction_type", "reason")
    search_fields = ("transaction_id", "wallet__user__email")
    readonly_fields = (
        "transaction_id",
        "wallet",
        "transaction_type",
        "amount",
        "balance_after",
        "reason",
        "description",
        "payment",
        "created_at",
    )
