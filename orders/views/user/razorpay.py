from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from orders.models import Order
from orders.service import InsufficientStockError, change_order_status, validate_snapshot_stock
from orders.service.order_helpers import create_items_from_snapshot
from orders.utils import get_payment_transaction
from payments.models import Transaction
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
      1. Verify the Razorpay signature
      2. If valid → create OrderItems from snapshot, deduct stock, confirm order
      3. If invalid → mark transaction and order as FAILED
    """
    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    razorpay_signature = request.POST.get("razorpay_signature", "")
    order_number = request.POST.get("order_number", "")

    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, order_number]):
        return JsonResponse({"error": "Missing payment data."}, status=400)

    try:
        txn = Transaction.objects.get(
            gateway_order_id=razorpay_order_id,
            user=request.user,
            status="PENDING",
        )
    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found."}, status=404)

    # ── Verify signature ──
    is_valid = verify_razorpay_signature(
        razorpay_order_id, razorpay_payment_id, razorpay_signature
    )

    if not is_valid:
        # Signature invalid → mark as failed
        txn.status = "FAILED"
        txn.note = f"Signature verification failed. Payment ID: {razorpay_payment_id}"
        txn.save(update_fields=["status", "note", "updated_at"])

        order = txn.content_object
        if order:
            change_order_status(order=order, to_status="FAILED")

        return JsonResponse({
            "success": False,
            "redirect_url": reverse("order_failure", args=[order_number]),
        })

    # ── Payment valid → create items + deduct stock ──
    order = txn.content_object
    if not order or not order.cart_snapshot:
        return JsonResponse({"error": "Order data not found."}, status=400)

    try:
        with transaction.atomic():
            # Mark payment as successful
            txn.gateway_payment_id = razorpay_payment_id
            txn.gateway_signature = razorpay_signature
            txn.status = "PAID"
            txn.save(update_fields=[
                "gateway_payment_id", "gateway_signature", "status", "updated_at",
            ])

            # Create items from snapshot (locks variants + validates stock)
            create_items_from_snapshot(
                order=order,
                snapshot=order.cart_snapshot,
                actor=request.user,
            )

            # Confirm order
            change_order_status(order=order, to_status="CONFIRMED")

            # Clear snapshot (no longer needed)
            order.cart_snapshot = None
            order.save(update_fields=["cart_snapshot"])

    except InsufficientStockError:
        # Stock sold out between order creation and payment
        # Payment was collected by Razorpay but order can't be fulfilled
        txn.status = "PAID"
        txn.gateway_payment_id = razorpay_payment_id
        txn.gateway_signature = razorpay_signature
        txn.note = "Payment collected but stock unavailable — refund initiated"
        txn.save(update_fields=[
            "status", "gateway_payment_id", "gateway_signature", "note", "updated_at",
        ])

        change_order_status(order=order, to_status="STOCK_UNAVAILABLE")

        initiate_refund(
            order=order,
            user=request.user,
            amount=order.grand_total,
            txn_type="REFUND",
            content_object=order,
            note=f"Auto-refund: stock unavailable after Razorpay payment for order {order.order_number}",
        )

        # Restore cart items and revoke coupon
        if order.cart_snapshot:
            _restore_cart_from_snapshot(request.user, order.cart_snapshot)
            order.cart_snapshot = None
            order.save(update_fields=["cart_snapshot"])

        if order.coupon:
            revoke_coupon_usage(order)

        return JsonResponse({
            "success": False,
            "redirect_url": reverse("order_failure", args=[order_number]),
        })

    return JsonResponse({
        "success": True,
        "redirect_url": reverse("order_success", args=[order_number]),
    })


@login_required
@require_POST
def razorpay_payment_failed(request):
    """
    Called when user dismisses the Razorpay popup or payment fails.
    Simply marks the transaction and order as FAILED.
    No stock to restore — items were never created.
    """
    order_number = request.POST.get("order_number", "")
    reason = request.POST.get("reason", "Payment cancelled by user")

    if not order_number:
        return JsonResponse({"error": "Missing order number."}, status=400)

    try:
        txn = Transaction.objects.get(
            content_type=ContentType.objects.get_for_model(Order),
            object_id=Order.objects.get(
                order_number=order_number, user=request.user
            ).pk,
            status="PENDING",
            payment_method="RAZORPAY",
        )
    except (Transaction.DoesNotExist, Order.DoesNotExist):
        return JsonResponse({"error": "Transaction not found."}, status=404)

    txn.status = "FAILED"
    txn.note = reason
    txn.save(update_fields=["status", "note", "updated_at"])

    order = txn.content_object
    if order:
        change_order_status(order=order, to_status="FAILED")

    return JsonResponse({
        "success": True,
        "redirect_url": reverse("order_failure", args=[order_number]),
    })


@login_required
@require_POST
def retry_razorpay_payment(request):
    """
    Retry a failed Razorpay payment from the order listing page.

    Flow:
      1. Validate the order is FAILED + RAZORPAY + has cart_snapshot
      2. Lock variants and check stock is still available
      3. Reset order status: FAILED → PLACED
      4. Create a new Razorpay order + Transaction
      5. Return JSON for the frontend to open Razorpay popup
    """
    order_number = request.POST.get("order_number", "")
    if not order_number:
        return JsonResponse({"error": "Missing order number."}, status=400)

    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Must be FAILED + RAZORPAY + has snapshot
    payment = get_payment_transaction(order)
    if (
        order.status != "FAILED"
        or not payment
        or payment.payment_method != "RAZORPAY"
        or not order.cart_snapshot
    ):
        return JsonResponse(
            {"error": "This order is not eligible for payment retry."},
            status=400,
        )

    try:
        with transaction.atomic():
            # Lock variants and validate stock from snapshot
            validate_snapshot_stock(order.cart_snapshot)

            # Reset order: FAILED → PLACED
            change_order_status(order=order, to_status="PLACED")

            # Mark old FAILED transaction as CANCELLED before creating new one (fix #14)
            if payment and payment.status == "FAILED":
                payment.status = "CANCELLED"
                payment.note = "Superseded by payment retry"
                payment.save(update_fields=["status", "note", "updated_at"])

            # Create new Razorpay order
            amount_paise = int(order.grand_total * 100)
            # Razorpay test mode: UPI capped at ₹1,00,000 — cap to ₹99,999
            # if settings.DEBUG:
            amount_paise = min(amount_paise, 99_999_00)
            rz_order = create_razorpay_order(
                amount_paise=amount_paise,
                receipt=order.order_number,
            )

            # Create new PENDING transaction
            txn = create_transaction(
                user=request.user,
                txn_type="ORDER_PAYMENT",
                method="RAZORPAY",
                amount=order.grand_total,
                status="PENDING",
                content_object=order,
                note=f"Retry payment for order {order.order_number}",
            )
            txn.gateway_order_id = rz_order["id"]
            txn.save(update_fields=["gateway_order_id"])

        return JsonResponse({
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
        })

    except InsufficientStockError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
