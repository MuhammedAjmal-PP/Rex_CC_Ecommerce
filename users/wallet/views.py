from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
from users.wallet.models import Wallet, WalletTransaction
from django.shortcuts import render

# Create your views here.
@login_required
@never_cache
def wallet_page(request):
    """User wallet page: balance + transaction history."""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    transactions = (
        WalletTransaction.objects.filter(wallet=wallet)
        .select_related("transaction")
        .order_by("-created_at")
    )

    page_obj = Paginator(transactions, 15).get_page(request.GET.get("page"))

    context = {
        "wallet": wallet,
        "transactions": page_obj,
        "page_obj": page_obj,
    }
    return render(request, "wallet/wallet.html", context)
