from django.urls import path
from users.wallet.views import wallet_page

urlpatterns = [
    path("wallet/", wallet_page, name="user_wallet"),
]
