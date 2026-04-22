from django.contrib import messages
from accounts.decorators import superuser_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from payments.models import Transaction
from payments.service import complete_refund, fail_refund
from django.shortcuts import render

# Create your views here.


# ──────────────────────────────────────────────────────────────
# ADMIN — TRANSACTION LIST
# ──────────────────────────────────────────────────────────────


@superuser_required
@never_cache
@require_GET
def transaction_list(request):
    """Paginated list of all transactions with search and filters."""
    search_query = request.GET.get("qs", "").strip()
    status_filter = request.GET.get("status", "all").strip().upper()
    type_filter = request.GET.get("type", "all").strip().upper()

    txns_qs = Transaction.objects.select_related("user").order_by("-created_at")

    if search_query:
        txns_qs = txns_qs.filter(
            Q(transaction_id__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(note__icontains=search_query)
        )

    if status_filter and status_filter != "ALL":
        txns_qs = txns_qs.filter(status=status_filter)

    if type_filter and type_filter != "ALL":
        txns_qs = txns_qs.filter(transaction_type=type_filter)

    # Stats
    all_txns = Transaction.objects.all()
    status_counts = {
        "total": all_txns.count(),
        "pending": all_txns.filter(status="PENDING").count(),
        "completed": all_txns.filter(status__in=["PAID", "COMPLETED"]).count(),
        "failed": all_txns.filter(status="FAILED").count(),
    }

    page_obj = Paginator(txns_qs, 20).get_page(request.GET.get("page"))

    context = {
        "transactions": page_obj,
        "status_counts": status_counts,
        "search_query": search_query,
        "status_filter": status_filter,
        "type_filter": type_filter,
    }
    return render(request, "payments/admin/transaction_list.html", context)


# ──────────────────────────────────────────────────────────────
# ADMIN — TRANSACTION DETAIL
# ──────────────────────────────────────────────────────────────


@superuser_required
@never_cache
@require_GET
def transaction_detail(request, txn_id):
    """Detail view for a single transaction."""
    txn = get_object_or_404(
        Transaction.objects.select_related("user", "content_type"),
        transaction_id=txn_id,
    )

    # Get linked object info
    linked_object = txn.content_object
    wallet_txn = getattr(txn, "wallet_transaction", None)

    context = {
        "txn": txn,
        "linked_object": linked_object,
        "wallet_txn": wallet_txn,
    }
    return render(request, "payments/admin/transaction_detail.html", context)


# ──────────────────────────────────────────────────────────────
# ADMIN — REFUND LIST
# ──────────────────────────────────────────────────────────────


@superuser_required
@never_cache
@require_GET
def refund_list(request):
    """Paginated list of refund transactions only."""
    search_query = request.GET.get("qs", "").strip()
    status_filter = request.GET.get("status", "all").strip().upper()

    refunds_qs = (
        Transaction.objects.filter(
            transaction_type__in=["CANCELLATION_REFUND", "RETURN_REFUND"]
        )
        .select_related("user")
        .order_by("-created_at")
    )

    if search_query:
        refunds_qs = refunds_qs.filter(
            Q(transaction_id__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
        )

    if status_filter and status_filter != "ALL":
        refunds_qs = refunds_qs.filter(status=status_filter)

    # Stats for refunds only
    all_refunds = Transaction.objects.filter(
        transaction_type__in=["CANCELLATION_REFUND", "RETURN_REFUND"]
    )
    status_counts = {
        "total": all_refunds.count(),
        "pending": all_refunds.filter(status="PENDING").count(),
        "completed": all_refunds.filter(status="COMPLETED").count(),
        "failed": all_refunds.filter(status="FAILED").count(),
    }

    page_obj = Paginator(refunds_qs, 20).get_page(request.GET.get("page"))

    context = {
        "refunds": page_obj,
        "status_counts": status_counts,
        "search_query": search_query,
        "status_filter": status_filter,
    }
    return render(request, "payments/admin/refund_list.html", context)


# ──────────────────────────────────────────────────────────────
# ADMIN — REFUND DETAIL
# ──────────────────────────────────────────────────────────────


@superuser_required
@never_cache
@require_GET
def refund_detail(request, txn_id):
    """Detail view for a single refund transaction with action buttons."""
    txn = get_object_or_404(
        Transaction.objects.select_related("user", "content_type"),
        transaction_id=txn_id,
        transaction_type__in=["CANCELLATION_REFUND", "RETURN_REFUND"],
    )

    linked_object = txn.content_object
    wallet_txn = getattr(txn, "wallet_transaction", None)

    context = {
        "txn": txn,
        "linked_object": linked_object,
        "wallet_txn": wallet_txn,
        "can_act": txn.status == "PENDING",
    }
    return render(request, "payments/admin/refund_detail.html", context)


# ──────────────────────────────────────────────────────────────
# ADMIN — REFUND ACTION (APPROVE / REJECT)
# ──────────────────────────────────────────────────────────────


@superuser_required
@never_cache
@require_POST
def refund_action(request, txn_id):
    """Approve or reject a pending refund transaction."""
    txn = get_object_or_404(
        Transaction,
        transaction_id=txn_id,
        transaction_type__in=["CANCELLATION_REFUND", "RETURN_REFUND"],
    )

    action = request.POST.get("action", "").strip().upper()
    fallback_url = reverse("admin_refund_detail", kwargs={"txn_id": txn.transaction_id})

    if txn.status != "PENDING":
        messages.error(request, "This refund is no longer pending.")
        return redirect(fallback_url)

    if action == "APPROVE":
        try:
            complete_refund(txn)
            messages.success(
                request,
                f"Refund approved — ₹{txn.amount:,.0f} credited to {txn.user.email}'s wallet.",
            )
        except Exception as e:
            messages.error(request, f"Failed to process refund: {e}")

    elif action == "REJECT":
        try:
            note = request.POST.get("note", "").strip()
            fail_refund(txn, note=note or "Rejected by admin")
            messages.success(request, "Refund rejected.")
        except Exception as e:
            messages.error(request, f"Failed to reject refund: {e}")
    else:
        messages.error(request, "Invalid action.")

    return redirect(fallback_url)
