from django.urls import path
from users.wallet.views import wallet_page, wallet_transaction_detail

urlpatterns = [
    path("wallet/", wallet_page, name="user_wallet"),
    path(
        "wallet/transaction/<uuid:transaction_id>/",
        wallet_transaction_detail,
        name="user_transaction_detail",
    ),
]
