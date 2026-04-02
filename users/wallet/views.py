from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction as db_transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from payments.models import Transaction
from payments.razorpay_service import create_razorpay_order, verify_razorpay_signature
from payments.service import create_transaction
from users.wallet.models import Wallet, WalletTransaction
from users.wallet.service import credit_wallet, get_or_create_wallet


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
        "topup_min": settings.WALLET_TOPUP_MIN,
        "topup_max": settings.WALLET_TOPUP_MAX,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
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


# ──────────────────────────────────────────────────────────────
# WALLET TOP-UP VIA RAZORPAY
# ──────────────────────────────────────────────────────────────


@login_required
@require_POST
def wallet_topup_initiate(request):
    """
    Step 1: User requests a wallet top-up.
      - Validates the amount (within configured limits)
      - Creates a Razorpay order
      - Creates a PENDING Transaction (WALLET_TOPUP / RAZORPAY)
      - Returns JSON for the frontend to open the Razorpay popup
    """
    raw_amount = request.POST.get("amount", "").strip()

    # ── Validate amount ──
    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, ValueError, TypeError):
        return JsonResponse({"error": "Please enter a valid amount."}, status=400)

    if amount < settings.WALLET_TOPUP_MIN:
        return JsonResponse(
            {"error": f"Minimum top-up amount is ₹{settings.WALLET_TOPUP_MIN:,}."},
            status=400,
        )

    if amount > settings.WALLET_TOPUP_MAX:
        return JsonResponse(
            {"error": f"Maximum top-up amount is ₹{settings.WALLET_TOPUP_MAX:,}."},
            status=400,
        )

    # ── Ensure wallet exists & is active ──
    wallet = get_or_create_wallet(request.user)
    if not wallet.is_active:
        return JsonResponse(
            {"error": "Your wallet is currently inactive."},
            status=400,
        )

    # ── Create Razorpay order ──
    amount_paise = int(amount * 100)
    try:
        rz_order = create_razorpay_order(
            amount_paise=amount_paise,
            receipt=f"WLT-{request.user.pk}",
        )
    except Exception as exc:
        return JsonResponse(
            {"error": f"Payment gateway error: {exc}"},
            status=500,
        )

    # ── Create PENDING transaction ──
    txn = create_transaction(
        user=request.user,
        txn_type="WALLET_TOPUP",
        method="RAZORPAY",
        amount=amount,
        status="PENDING",
        content_object=wallet,
        note=f"Wallet top-up ₹{amount:,.2f}",
    )
    txn.gateway_order_id = rz_order["id"]
    txn.save(update_fields=["gateway_order_id"])

    return JsonResponse(
        {
            "success": True,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "razorpay_order_id": rz_order["id"],
            "amount": rz_order["amount"],
            "currency": rz_order["currency"],
            "name": "REX CC",
            "description": f"Wallet Top-up — ₹{amount:,.0f}",
            "prefill": {
                "email": request.user.email,
                "contact": str(request.user.phone_number or ""),
            },
        }
    )


@login_required
@require_POST
def wallet_topup_callback(request):
    """
    Step 2 (success): Razorpay popup completed successfully.
      - Verifies the payment signature
      - Credits the wallet
      - Marks transaction as PAID
    """
    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    razorpay_signature = request.POST.get("razorpay_signature", "")

    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return JsonResponse({"error": "Missing payment data."}, status=400)

    try:
        txn = Transaction.objects.get(
            gateway_order_id=razorpay_order_id,
            user=request.user,
            transaction_type="WALLET_TOPUP",
            status="PENDING",
        )
    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found."}, status=404)

    # ── Verify signature ──
    is_valid = verify_razorpay_signature(
        razorpay_order_id, razorpay_payment_id, razorpay_signature
    )

    if not is_valid:
        txn.status = "FAILED"
        txn.note = f"Signature verification failed. Payment ID: {razorpay_payment_id}"
        txn.save(update_fields=["status", "note", "updated_at"])
        return JsonResponse(
            {"error": "Payment verification failed."},
            status=400,
        )

    # ── Payment valid → credit wallet ──
    try:
        with db_transaction.atomic():
            txn.gateway_payment_id = razorpay_payment_id
            txn.gateway_signature = razorpay_signature
            txn.status = "PAID"
            txn.save(
                update_fields=[
                    "gateway_payment_id",
                    "gateway_signature",
                    "status",
                    "updated_at",
                ]
            )

            credit_wallet(
                user=request.user,
                amount=txn.amount,
                transaction_obj=txn,
            )

        # Fetch updated balance
        wallet = get_or_create_wallet(request.user)
        wallet.refresh_from_db()

        return JsonResponse(
            {
                "success": True,
                "new_balance": str(wallet.balance),
            }
        )

    except Exception as exc:
        return JsonResponse(
            {"error": f"Failed to credit wallet: {exc}"},
            status=500,
        )


@login_required
@require_POST
def wallet_topup_failed(request):
    """
    Step 2 (failure): Razorpay popup dismissed or payment failed.
      - Marks the PENDING transaction as FAILED.
    """
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    reason = request.POST.get("reason", "Payment cancelled by user")

    if not razorpay_order_id:
        return JsonResponse({"error": "Missing order ID."}, status=400)

    try:
        txn = Transaction.objects.get(
            gateway_order_id=razorpay_order_id,
            user=request.user,
            transaction_type="WALLET_TOPUP",
            status="PENDING",
        )
    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found."}, status=404)

    txn.status = "FAILED"
    txn.note = reason
    txn.save(update_fields=["status", "note", "updated_at"])

    return JsonResponse({"success": True})
