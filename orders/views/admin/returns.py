from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from catalog.service import update_stock
from orders.models import Return
from orders.service import (
    InvalidTransitionError,
    change_order_item_status,
)
from orders.utils import compute_return_refund
from coupons.service import revoke_coupon_if_invalid
from payments.service import initiate_refund

# Return model status transitions allowed by admin
RETURN_ALLOWED_TRANSITIONS = {
    "REQUESTED": {"APPROVED", "REJECTED"},
    "APPROVED": {"COMPLETED"},
    "REJECTED": set(),
    "COMPLETED": set(),
}


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
@require_GET
def return_list(request):
    """Paginated list of all return requests with search and status filter."""
    search_query = request.GET.get("qs", "").strip()
    status_filter = request.GET.get("status", "all").strip().upper()

    returns_qs = (
        Return.objects.select_related(
            "order_item",
            "order_item__order",
            "order_item__order__user",
            "order_item__product_variant",
            "order_item__product_variant__product",
        )
        .prefetch_related("images", "transactions")
        .order_by("-created_at")
    )

    if search_query:
        returns_qs = returns_qs.filter(
            Q(return_number__icontains=search_query)
            | Q(order_item__order__order_number__icontains=search_query)
            | Q(order_item__order__user__email__icontains=search_query)
        )

    if status_filter != "ALL":
        returns_qs = returns_qs.filter(status=status_filter)

    # Status counts — single aggregate query (P1 fix)
    counts = Return.objects.aggregate(
        total=Count("id"),
        requested=Count("id", filter=Q(status="REQUESTED")),
        approved=Count("id", filter=Q(status="APPROVED")),
        rejected=Count("id", filter=Q(status="REJECTED")),
        completed=Count("id", filter=Q(status="COMPLETED")),
    )

    paginator = Paginator(returns_qs, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "returns": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_counts": counts,
    }
    return render(request, "orders/admin/return_list.html", context)


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
@require_GET
def return_detail(request, return_number):
    """Detail view for a single return request."""
    return_obj = get_object_or_404(
        Return.objects.select_related(
            "order_item",
            "order_item__order",
            "order_item__order__user",
            "order_item__product_variant",
            "order_item__product_variant__product",
        ).prefetch_related("images", "transactions"),
        return_number=return_number,
    )

    current_status = return_obj.status
    allowed_next = sorted(RETURN_ALLOWED_TRANSITIONS.get(current_status, set()))

    context = {
        "return_obj": return_obj,
        "order_item": return_obj.order_item,
        "order": return_obj.order_item.order,
        "images": return_obj.images.all(),
        "allowed_next_statuses": allowed_next,
        "refund_transactions": return_obj.transactions.all(),
    }
    return render(request, "orders/admin/return_detail.html", context)


@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
@never_cache
@require_POST
def return_status_update(request, return_number):
    """
    Handle return status transitions:
      APPROVE  → Return APPROVED (OrderItem stays RETURN_REQUESTED)
      REJECT   → Return REJECTED, OrderItem reverted to DELIVERED
      COMPLETE → Return COMPLETED, OrderItem → RETURNED, stock restored
    """
    return_obj = get_object_or_404(
        Return.objects.select_related(
            "order_item",
            "order_item__product_variant",
            "order_item__order",
        ),
        return_number=return_number,
    )

    action = request.POST.get("action", "").strip().upper()
    admin_note = request.POST.get("admin_note", "").strip()
    order_item = return_obj.order_item
    fallback_url = reverse("admin_return_detail", args=[return_number])

    # ── APPROVE ──────────────────────────────────────
    if action == "APPROVE":
        if return_obj.status != "REQUESTED":
            messages.error(request, "Only REQUESTED returns can be approved.")
            return redirect(fallback_url)

        return_obj.status = "APPROVED"
        if admin_note:
            return_obj.admin_note = admin_note
        return_obj.save(update_fields=["status", "admin_note"])

        messages.success(request, f"Return {return_obj.return_number} approved.")

    # ── REJECT ───────────────────────────────────────
    elif action == "REJECT":
        if return_obj.status != "REQUESTED":
            messages.error(request, "Only REQUESTED returns can be rejected.")
            return redirect(fallback_url)

        if not admin_note:
            messages.error(request, "Admin note is required when rejecting a return.")
            return redirect(fallback_url)

        return_obj.status = "REJECTED"
        return_obj.admin_note = admin_note
        return_obj.save(update_fields=["status", "admin_note"])

        # Revert OrderItem status: RETURN_REQUESTED → DELIVERED
        try:
            change_order_item_status(order_item=order_item, to_status="DELIVERED")
        except InvalidTransitionError as error:
            messages.warning(
                request,
                f"Return rejected but item status could not be reverted: {error}",
            )
            return redirect(fallback_url)

        messages.success(request, f"Return {return_obj.return_number} rejected.")

    # ── COMPLETE ─────────────────────────────────────
    elif action == "COMPLETE":
        if return_obj.status != "APPROVED":
            messages.error(request, "Only APPROVED returns can be completed.")
            return redirect(fallback_url)

        try:
            with transaction.atomic():
                return_obj.status = "COMPLETED"
                if admin_note:
                    return_obj.admin_note = admin_note
                return_obj.save(update_fields=["status", "admin_note"])

                refund_amount = compute_return_refund(order_item)

                # Transition OrderItem status: RETURN_REQUESTED → RETURNED
                change_order_item_status(order_item=order_item, to_status="RETURNED")

                # Restore stock
                update_stock(
                    product_variant=order_item.product_variant,
                    change=+order_item.quantity,
                    reason="RETURNED",
                    actor=request.user,
                    reference_object=return_obj,
                    note=f"Stock restored — return {return_obj.return_number} completed",
                )

                # Create PENDING refund transaction
                order = order_item.order
                initiate_refund(
                    order=order,
                    user=order.user,
                    amount=refund_amount,
                    txn_type="RETURN_REFUND",
                    content_object=return_obj,
                    note=f"Return refund — return #{return_obj.return_number}",
                )

                # Revoke coupon if remaining items no longer qualify
                revoke_coupon_if_invalid(order)

        except InvalidTransitionError as error:
            messages.warning(
                request,
                f"Return completed but item status could not be updated: {error}",
            )
            return redirect(fallback_url)

        messages.success(
            request,
            f"Return {return_obj.return_number} completed. "
            f"Stock restored (+{order_item.quantity}). "
            f"Refund of ₹{refund_amount} is pending admin approval.",
        )

    else:
        messages.error(request, f"Unknown action: {action}")

    return redirect(fallback_url)
