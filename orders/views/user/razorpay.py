from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from orders.models import Order
from orders.service import (
    InsufficientStockError,
    change_order_status,
    validate_snapshot_stock,
)
from orders.service.order_helpers import create_items_from_snapshot
from payments.service import create_transaction, initiate_refund
from payments.razorpay_service import create_razorpay_order, verify_razorpay_signature
from coupons.service import revoke_coupon_usage
from orders.tasks import _restore_cart_from_snapshot


@login_required
@require_POST
def razorpay_callback(request):
    """
    Called after Razorpay checkout popup succeeds.

    Flow:
      1. Look up the PENDING_PAYMENT order by order_number
      2. Verify the Razorpay signature
      3. If valid → create Transaction (PAID), create OrderItems from snapshot,
         deduct stock, confirm order
      4. If invalid → create Transaction (FAILED), mark order as FAILED
    """
    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    razorpay_signature = request.POST.get("razorpay_signature", "")
    order_number = request.POST.get("order_number", "")

    if not all(
        [razorpay_payment_id, razorpay_order_id, razorpay_signature, order_number]
    ):
        return JsonResponse({"error": "Missing payment data."}, status=400)

    try:
        order = Order.objects.get(
            order_number=order_number,
            user=request.user,
            status="PENDING_PAYMENT",
        )
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found."}, status=404)

    # Verify that the Razorpay order ID matches what we stored
    if order.gateway_order_id != razorpay_order_id:
        return JsonResponse({"error": "Order mismatch."}, status=400)

    # ── Verify signature ──
    is_valid = verify_razorpay_signature(
        razorpay_order_id, razorpay_payment_id, razorpay_signature
    )

    # ── Create transaction once with common fields ──
    txn = create_transaction(
        user=request.user,
        txn_type="ORDER_PAYMENT",
        method="RAZORPAY",
        amount=order.grand_total,
        status="PAID" if is_valid else "FAILED",
        content_object=order,
        note="",
    )
    txn.gateway_order_id = razorpay_order_id
    txn.gateway_payment_id = razorpay_payment_id

    if not is_valid:
        # Signature invalid → mark transaction and order as FAILED
        txn.note = f"Signature verification failed. Payment ID: {razorpay_payment_id}"
        txn.save(update_fields=["gateway_order_id", "gateway_payment_id", "note", "updated_at"])

        change_order_status(order=order, to_status="FAILED")

        return JsonResponse(
            {
                "success": False,
                "redirect_url": reverse("order_failure", args=[order_number]),
            }
        )

    # ── Signature valid → save gateway fields ──
    txn.gateway_signature = razorpay_signature
    txn.note = f"Razorpay payment for order {order.order_number}"
    txn.save(
        update_fields=[
            "gateway_order_id",
            "gateway_payment_id",
            "gateway_signature",
            "note",
            "updated_at",
        ]
    )

    if not order.cart_snapshot:
        return JsonResponse({"error": "Order data not found."}, status=400)

    try:
        with transaction.atomic():
            # Create items from snapshot (locks variants + validates stock)
            create_items_from_snapshot(
                order=order,
                snapshot=order.cart_snapshot,
                actor=request.user,
            )

            # Confirm order
            change_order_status(order=order, to_status="CONFIRMED")

            # Clear snapshot and gateway_order_id (no longer needed)
            order.cart_snapshot = None
            order.gateway_order_id = ""
            order.save(update_fields=["cart_snapshot", "gateway_order_id"])

    except InsufficientStockError:
        # Stock sold out — payment was collected but order can't be fulfilled
        txn.note = "Payment collected but stock unavailable — refund initiated"
        txn.save(update_fields=["note", "updated_at"])

        change_order_status(order=order, to_status="STOCK_UNAVAILABLE")

        initiate_refund(
            order=order,
            user=request.user,
            amount=order.grand_total,
            txn_type="CANCELLATION_REFUND",
            content_object=order,
            note=f"Auto-refund: stock unavailable after Razorpay payment for order {order.order_number}",
        )

        # Restore cart items and revoke coupon
        if order.cart_snapshot:
            _restore_cart_from_snapshot(request.user, order.cart_snapshot)
            order.cart_snapshot = None
            order.gateway_order_id = ""
            order.save(update_fields=["cart_snapshot", "gateway_order_id"])

        if order.coupon:
            revoke_coupon_usage(order)

        return JsonResponse(
            {
                "success": False,
                "redirect_url": reverse("order_failure", args=[order_number]),
            }
        )

    return JsonResponse(
        {
            "success": True,
            "redirect_url": reverse("order_success", args=[order_number]),
        }
    )


@login_required
@require_POST
def razorpay_payment_failed(request):
    """
    Called when user dismisses the Razorpay popup or payment fails.
    Creates a FAILED transaction and marks the order as FAILED.
    No stock to restore — items were never created.
    """
    order_number = request.POST.get("order_number", "")
    reason = request.POST.get("reason", "Payment cancelled by user")

    if not order_number:
        return JsonResponse({"error": "Missing order number."}, status=400)

    try:
        order = Order.objects.get(
            order_number=order_number,
            user=request.user,
            status="PENDING_PAYMENT",
        )
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found."}, status=404)

    # Create FAILED transaction
    txn = create_transaction(
        user=request.user,
        txn_type="ORDER_PAYMENT",
        method="RAZORPAY",
        amount=order.grand_total,
        status="FAILED",
        content_object=order,
        note=reason,
    )
    txn.gateway_order_id = order.gateway_order_id
    txn.save(update_fields=["gateway_order_id"])

    change_order_status(order=order, to_status="FAILED")

    return JsonResponse(
        {
            "success": True,
            "redirect_url": reverse("order_failure", args=[order_number]),
        }
    )


@login_required
@require_POST
def retry_razorpay_payment(request):
    """
    Retry a failed Razorpay payment from the order listing page.

    Flow:
      1. Validate the order is FAILED + has cart_snapshot
      2. Lock variants and check stock is still available
      3. Create a new Razorpay order via API
      4. Reset order status: FAILED → PENDING_PAYMENT
      5. Store new gateway_order_id on Order
      6. Return JSON for the frontend to open Razorpay popup
    """
    order_number = request.POST.get("order_number", "")
    if not order_number:
        return JsonResponse({"error": "Missing order number."}, status=400)

    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Must be FAILED + has snapshot (Razorpay order that can be retried)
    if order.status != "FAILED" or not order.cart_snapshot:
        return JsonResponse(
            {"error": "This order is not eligible for payment retry."},
            status=400,
        )

    try:
        with transaction.atomic():
            # Lock variants and validate stock from snapshot
            validate_snapshot_stock(order.cart_snapshot)

            # Reset order: FAILED → PENDING_PAYMENT
            change_order_status(order=order, to_status="PENDING_PAYMENT")

            # Create new Razorpay order
            amount_paise = int(order.grand_total * 100)
            # Razorpay test mode: UPI capped at ₹1,00,000 — cap to ₹99,999
            # if settings.DEBUG:
            amount_paise = min(amount_paise, 99_999_00)
            rz_order = create_razorpay_order(
                amount_paise=amount_paise,
                receipt=order.order_number,
            )

            # Store new gateway_order_id on Order (no Transaction created)
            order.gateway_order_id = rz_order["id"]
            order.save(update_fields=["gateway_order_id"])

        return JsonResponse(
            {
                "success": True,
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "razorpay_order_id": rz_order["id"],
                "amount": rz_order["amount"],
                "currency": rz_order["currency"],
                "name": "REX CC",
                "description": f"Retry payment for Order #{order.order_number}",
                "order_number": order.order_number,
                "prefill": {
                    "email": request.user.email,
                    "contact": str(request.user.phone_number or ""),
                },
            }
        )

    except InsufficientStockError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
