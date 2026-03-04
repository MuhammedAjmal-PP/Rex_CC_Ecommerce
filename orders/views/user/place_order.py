from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from catalog.service import update_stock
from orders.models import Order, OrderItem
from payments.models import Transaction
from payments.service import create_transaction
from payments.razorpay_service import create_razorpay_order, verify_razorpay_signature
from users.cart.models import Cart, CartItem
from users.cart.utils import compute_cart_summary
from users.user_profile.models import Address
from users.wallet.service import (
    can_pay_with_wallet,
    debit_wallet,
)
from orders.service import (
    InsufficientStockError,
    change_order_item_status,
    change_order_status,
    lock_variants_for_update,
    restore_order_stock,
    validate_stock,
)
from coupons.service import (
    InvalidCouponError,
    validate_coupon,
    apply_coupon_to_order,
)




@login_required
@require_POST
def place_order_view(request):
    """
    Place order — handles COD, WALLET, and RAZORPAY.
    For RAZORPAY: returns JSON with Razorpay order data instead of redirect.
    """

    address_id = request.POST.get("address_id")
    payment_method = request.POST.get("payment_method")

    if not address_id or not payment_method:
        return HttpResponseBadRequest("Invalid request")

    ALLOWED_METHODS = {"COD", "WALLET", "RAZORPAY"}

    if payment_method not in ALLOWED_METHODS:
        return HttpResponseBadRequest(f"Unsupported payment method: {payment_method}")

    shipping_address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user,
        is_active=True,
    )

    billing_address = Address.objects.filter(
        user=request.user,
        is_default=True,
        is_active=True,
    ).first()

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        if payment_method == "RAZORPAY":
            return JsonResponse({"error": "Your cart is empty."}, status=400)
        messages.error(request, "Your cart is empty.")
        return redirect("user_cart")

    # Compute cart summary (packs variants, computes all totals)
    summary = compute_cart_summary(cart)

    if summary["items_count"] == 0:
        if payment_method == "RAZORPAY":
            return JsonResponse({"error": "Your cart is empty."}, status=400)
        messages.error(request, "Your cart is empty.")
        return redirect("user_cart")

    # Pre-check wallet balance to avoid database lock if insufficient
    if payment_method == "WALLET":
        if not can_pay_with_wallet(request.user, summary["grand_total"]):
            messages.error(
                request,
                "Insufficient wallet balance. Please choose another payment method.",
            )
            return redirect(reverse("checkout") + "?step=2")

    # ── Coupon re-validation (server-side) ──────────────────
    applied_coupon_session = request.session.get("applied_coupon")
    coupon_obj = None
    coupon_discount = Decimal("0.00")

    if applied_coupon_session:
        coupon_code = applied_coupon_session.get("code", "")
        try:
            coupon_obj, coupon_discount = validate_coupon(
                coupon_code, request.user, summary["sub_total"]
            )
        except InvalidCouponError as e:
            # Coupon no longer valid — clear session and redirect
            if "applied_coupon" in request.session:
                del request.session["applied_coupon"]
                request.session.modified = True
            if payment_method == "RAZORPAY":
                return JsonResponse(
                    {"error": f"Coupon '{coupon_code}' is no longer valid: {e}"},
                    status=400,
                )
            messages.error(request, f"Coupon '{coupon_code}' is no longer valid: {e}")
            return redirect("checkout")

    # Calculate adjusted grand total with correct flow:
    # sub_total → coupon → shipping → tax → grand_total
    adjusted_sub = summary["sub_total"] - coupon_discount
    if adjusted_sub < Decimal("0.00"):
        adjusted_sub = Decimal("0.00")
    adjusted_total_amount = adjusted_sub + summary["shipping_fee"]
    adjusted_tax = (adjusted_total_amount * Decimal(settings.GST_RATE) / Decimal("100")).quantize(Decimal("0.01"))
    adjusted_grand_total = adjusted_total_amount + adjusted_tax

    # Re-check wallet with adjusted total
    if payment_method == "WALLET" and coupon_obj:
        if not can_pay_with_wallet(request.user, adjusted_grand_total):
            messages.error(
                request,
                "Insufficient wallet balance. Please choose another payment method.",
            )
            return redirect(reverse("checkout") + "?step=2")
    # ────────────────────────────────────────────────────────

    with transaction.atomic():
        # Re-fetch cart items for stock locking (need fresh queryset)
        cart_items = CartItem.objects.filter(cart=cart).select_related("product_variant")
        locked_variants = lock_variants_for_update(items=cart_items)

        try:
            validate_stock(items=cart_items, stock_lookup=locked_variants)
        except InsufficientStockError as error:
            if payment_method == "RAZORPAY":
                return JsonResponse({"error": str(error)}, status=400)
            messages.error(request, str(error))
            return redirect("user_cart")

        # 1 create the order
        order = Order.objects.create(
            user=request.user,
            billing_address=billing_address.snapshot,
            shipping_address=shipping_address.snapshot,
            total=summary["total"],
            sub_total=summary["sub_total"],
            tax=adjusted_tax if coupon_obj else summary["tax"],
            discount=summary["discount"],
            shipping_fee=summary["shipping_fee"],
            grand_total=adjusted_grand_total,
            coupon=coupon_obj,
            coupon_discount=coupon_discount,
        )

        # Build price lookup from packed variants
        packed_prices = {
            ci.product_variant_id: ci.product_variant.final_price
            for ci in summary["cart_items"]
        }

        for item in cart_items:
            locked_variant = locked_variants[item.product_variant_id]

            # 2 create orderitems
            order_item = OrderItem.objects.create(
                order=order,
                product_variant=locked_variant,
                quantity=item.quantity,
                price=packed_prices.get(item.product_variant_id, locked_variant.price),  # discounted final price
                original_price=locked_variant.price,          # MRP at time of order
            )

            # 3 Initial ORDER ITEM status

            change_order_item_status(
                order_item=order_item,
                to_status="PENDING",
                note="Item pending fulfillment",
                actor=request.user,
            )

            # 4 update the stock and add entry to inventory log
            update_stock(
                product_variant=locked_variant,
                change=-item.quantity,
                reason="ORDER_PLACED",
                actor=request.user,
                reference_object=order_item,
                note=f"Order {order.order_number} placed",
            )

        # 5 Initial ORDER status
        if payment_method == "WALLET":
            change_order_status(
                order=order,
                to_status="CONFIRMED",
                note="Order placed by customer (wallet payment)",
                actor=request.user,
            )
        else:
            # COD and RAZORPAY start as PLACED
            # COD stays PLACED until admin confirms
            # RAZORPAY moves to CONFIRMED after successful payment callback
            change_order_status(
                order=order,
                to_status="PLACED",
                note="Order placed by customer",
                actor=request.user,
            )

        # 6 Payment handling
        if payment_method == "WALLET":
            txn = create_transaction(
                user=request.user,
                txn_type="ORDER_PAYMENT",
                method="WALLET",
                amount=order.grand_total,
                status="PAID",
                content_object=order,
                note=f"Wallet payment for order {order.order_number}",
            )
            debit_wallet(
                user=request.user,
                amount=order.grand_total,
                transaction_obj=txn,
            )

        elif payment_method == "COD":
            txn = create_transaction(
                user=request.user,
                txn_type="ORDER_PAYMENT",
                method="COD",
                amount=order.grand_total,
                status="PENDING",
                content_object=order,
                note=f"COD payment for order {order.order_number}",
            )

        elif payment_method == "RAZORPAY":
            txn = create_transaction(
                user=request.user,
                txn_type="ORDER_PAYMENT",
                method="RAZORPAY",
                amount=order.grand_total,
                status="PENDING",
                content_object=order,
                note=f"Razorpay payment for order {order.order_number}",
            )

            # Create Razorpay order via API
            amount_paise = int(order.grand_total * 100)
            rz_order = create_razorpay_order(amount_paise, order.order_number)
            txn.gateway_order_id = rz_order["id"]
            txn.save(update_fields=["gateway_order_id"])

        # Payment is auto-linked via content_object=order in create_transaction

        # 7 Clear cart
        cart_items.delete()

        # 8 Apply coupon usage
        if coupon_obj:
            apply_coupon_to_order(coupon_obj, request.user, order)
            if "applied_coupon" in request.session:
                del request.session["applied_coupon"]
                request.session.modified = True

    # For Razorpay, return JSON so frontend can launch the checkout modal
    if payment_method == "RAZORPAY":
        return JsonResponse(
            {
                "razorpay_order_id": txn.gateway_order_id,
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "amount": amount_paise,
                "order_number": order.order_number,
                "currency": "INR",
                "name": "REX CC",
                "description": f"Order {order.order_number}",
                "prefill": {
                    "name": request.user.get_full_name,
                    "email": request.user.email,
                },
            }
        )

    return redirect("order_success", order_number=order.order_number)


@csrf_exempt
@login_required
@require_POST
def razorpay_callback(request):
    """
    Razorpay payment callback — verifies signature and completes the transaction.
    Called via AJAX from the frontend after Razorpay checkout success.
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
        txn = Transaction.objects.get(
            gateway_order_id=razorpay_order_id,
            user=request.user,
            status="PENDING",
        )
    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found."}, status=404)

    # Verify signature
    is_valid = verify_razorpay_signature(
        razorpay_order_id, razorpay_payment_id, razorpay_signature
    )

    if is_valid:
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

        # Move order from PLACED → CONFIRMED now that payment is verified
        order = txn.content_object
        if order:
            change_order_status(
                order=order,
                to_status="CONFIRMED",
                note="Payment verified via Razorpay",
                actor=request.user,
            )

        return JsonResponse(
            {
                "success": True,
                "redirect_url": reverse("order_success", args=[order_number]),
            }
        )
    else:
        txn.status = "FAILED"
        txn.note = f"Signature verification failed. Payment ID: {razorpay_payment_id}"
        txn.save(update_fields=["status", "note", "updated_at"])

        # Mark order as FAILED and restore stock
        order = txn.content_object
        if order:
            change_order_status(
                order=order,
                to_status="FAILED",
                note="Payment verification failed",
                actor=txn.user,
            )
            restore_order_stock(order, actor=txn.user)

        return JsonResponse(
            {
                "success": False,
                "redirect_url": reverse("order_failure", args=[order_number]),
            }
        )


@csrf_exempt
@login_required
@require_POST
def razorpay_payment_failed(request):
    """
    Mark a Razorpay transaction as FAILED.
    Called when user dismisses the modal or Razorpay reports payment.failed.
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

    # Mark order as FAILED and restore stock
    order = txn.content_object
    if order:
        change_order_status(
            order=order,
            to_status="FAILED",
            note=f"Payment failed: {reason}",
            actor=request.user,
        )
        restore_order_stock(order, actor=request.user)

    return JsonResponse(
        {
            "success": True,
            "redirect_url": reverse("order_failure", args=[order_number]),
        }
    )


@login_required
@never_cache
def order_success_view(request, order_number):
    """Order success page — shows order summary details."""

    order = get_object_or_404(
        Order.objects.prefetch_related("payment"),
        user=request.user,
        order_number=order_number,
    )

    current_status = order.current_status.status

    # Sanity check: order must be in a valid post-placement state
    payment = order.payment_transaction
    if payment:
        if payment.payment_method == "COD" and current_status != "PLACED":
            return redirect("user_order_list")
        elif payment.payment_method != "COD" and current_status != "CONFIRMED":
            return redirect("user_order_list")

    return render(
        request,
        "orders/user/order_success.html",
        {
            "order": order,
        },
    )


@login_required
@never_cache
def order_failure_view(request, order_number):
    """Order failure page — shown when payment fails."""

    order = get_object_or_404(
        Order.objects.prefetch_related("payment"),
        user=request.user,
        order_number=order_number,
    )

    payment = order.payment_transaction
    is_razorpay_failed = (
        order.current_status
        and order.current_status.status == "FAILED"
        and payment
        and payment.payment_method == "RAZORPAY"
    )

    return render(
        request,
        "orders/user/order_failure.html",
        {
            "order": order,
            "is_razorpay_failed": is_razorpay_failed,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID if is_razorpay_failed else None,
        },
    )


@csrf_exempt
@login_required
@require_POST
def retry_razorpay_payment(request):
    """
    Retry a failed Razorpay payment.
    1. Validates the order is FAILED + RAZORPAY
    2. Validates stock is still available
    3. Resets order → PLACED, items → PENDING
    4. Creates a new Razorpay order + Transaction
    5. Returns JSON for the frontend to open Razorpay checkout
    """
    order_number = request.POST.get("order_number", "")
    if not order_number:
        return JsonResponse({"error": "Missing order number."}, status=400)

    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Validate order is in FAILED state and was RAZORPAY
    current_status = order.current_status
    payment = order.payment_transaction
    if (
        not current_status
        or current_status.status != "FAILED"
        or not payment
        or payment.payment_method != "RAZORPAY"
    ):
        return JsonResponse(
            {"error": "This order is not eligible for payment retry."},
            status=400,
        )

    # Validate stock & lock variants
    items = order.items.select_related("product_variant").all()

    try:
        with transaction.atomic():
            # Lock variants for update to prevent race conditions
            locked_variants = lock_variants_for_update(items=items)
            validate_stock(items=items, stock_lookup=locked_variants)
            # Reset order status: FAILED → PLACED
            change_order_status(
                order=order,
                to_status="PLACED",
                note="Payment retry initiated",
                actor=request.user,
            )

            # Reset item statuses: FAILED → PENDING
            for item in items:
                item_status = item.current_status
                if item_status and item_status.status == "FAILED":
                    change_order_item_status(
                        order_item=item,
                        to_status="PENDING",
                        note="Payment retry initiated",
                        actor=request.user,
                    )

            # Re-deduct stock (was restored when payment failed)
            for item in items:
                if item.product_variant:
                    update_stock(
                        product_variant=item.product_variant,
                        change=-item.quantity,
                        reason="ORDER_PLACED",
                        actor=request.user,
                        reference_object=item,
                        note=f"Stock re-deducted — payment retry for order {order.order_number}",
                    )

            # Create a new Razorpay order (old one is expired)
            amount_paise = int(order.grand_total * 100)
            rz_order = create_razorpay_order(
                amount_paise=amount_paise,
                receipt=order.order_number,
            )

            # Create a new PENDING transaction
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

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
