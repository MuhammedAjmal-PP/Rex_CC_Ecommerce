from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache

from payments.models import Transaction
from users.wallet.models import Wallet, WalletTransaction


@login_required
@never_cache
def wallet_page(request):
    """User wallet page: balance + transaction history with tab toggle."""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    active_tab = request.GET.get("tab", "wallet")
    if active_tab not in ("wallet", "all"):
        active_tab = "wallet"

    if active_tab == "wallet":
        qs = (
            WalletTransaction.objects.filter(wallet=wallet)
            .select_related("transaction")
            .order_by("-created_at")
        )
    else:
        qs = Transaction.objects.filter(user=request.user).order_by("-created_at")

    page_obj = Paginator(qs, 15).get_page(request.GET.get("page"))

    context = {
        "wallet": wallet,
        "transactions": page_obj,
        "page_obj": page_obj,
        "active_tab": active_tab,
    }
    return render(request, "wallet/wallet.html", context)


@login_required
@never_cache
def wallet_transaction_detail(request, transaction_id):
    """User-side transaction detail page."""
    txn = get_object_or_404(
        Transaction.objects.select_related("content_type"),
        user=request.user,
        transaction_id=transaction_id,
    )

    # Check if there's a linked wallet transaction
    wallet_txn = (
        WalletTransaction.objects.filter(
            transaction=txn,
        )
        .select_related("wallet")
        .first()
    )

    # Resolve linked object info
    linked_obj = None
    if txn.content_type and txn.object_id:
        try:
            linked_obj = txn.content_object
        except Exception:
            linked_obj = None

    context = {
        "txn": txn,
        "wallet_txn": wallet_txn,
        "linked_obj": linked_obj,
    }
    return render(request, "wallet/transaction_detail.html", context)
