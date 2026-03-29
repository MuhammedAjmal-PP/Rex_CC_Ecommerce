from django.contrib import admin
from users.wallet.models import Wallet, WalletTransaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("user__email",)
    # readonly_fields = ("user", "balance", "is_active", "created_at", "updated_at")
    list_per_page = 25


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "wallet",
        "label",
        "transaction",
        "balance_before",
        "balance_after",
        "created_at",
    )
    list_filter = ("label", "created_at")
    search_fields = ("wallet__user__email",)
    readonly_fields = (
        "transaction",
        "wallet",
        "label",
        "balance_before",
        "balance_after",
        "created_at",
    )
    list_per_page = 25
