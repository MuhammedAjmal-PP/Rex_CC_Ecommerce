from django.urls import path
from users.wallet.views import (
    wallet_page,
    wallet_transaction_detail,
    wallet_topup_initiate,
    wallet_topup_callback,
    wallet_topup_failed,
)

urlpatterns = [
    path("wallet/", wallet_page, name="user_wallet"),
    path(
        "wallet/transaction/<str:transaction_id>/",
        wallet_transaction_detail,
        name="user_transaction_detail",
    ),
    # ── Wallet Top-up (Razorpay) ──
    path("wallet/topup/initiate/", wallet_topup_initiate, name="wallet_topup_initiate"),
    path("wallet/topup/callback/", wallet_topup_callback, name="wallet_topup_callback"),
    path("wallet/topup/failed/", wallet_topup_failed, name="wallet_topup_failed"),
]
