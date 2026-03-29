"""
Place order view — handles COD, WALLET, and RAZORPAY order placement.
"""

from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from catalog.service import update_stock
from orders.models import Order, OrderItem
from orders.service import (
    InsufficientStockError,
    change_order_status,
    lock_variants_for_update,
    validate_stock,
)
from orders.service.order_helpers import build_cart_snapshot
from payments.service import create_transaction
from payments.razorpay_service import create_razorpay_order
from users.cart.models import Cart, CartItem
from users.cart.utils import compute_cart_summary
from users.user_profile.models import Address
from users.wallet.service import can_pay_with_wallet, debit_wallet
from coupons.service import (
    InvalidCouponError,
    validate_coupon_locked,
    apply_coupon_to_order,
    recalculate_with_coupon,
)


@login_required
@require_POST
def place_order_view(request):
    """
    Place order — main entry point.

    COD / WALLET: single atomic block — order + items + stock + cart clear.
    RAZORPAY:     two-phase — order shell + snapshot only, items created on callback.
    """

    # ── 1. Validate inputs ────────────────────
    address_id = request.POST.get("address_id")
    payment_method = request.POST.get("payment_method")

    if not address_id or not payment_method:
        return HttpResponseBadRequest("Invalid request")

    if payment_method not in {"COD", "WALLET", "RAZORPAY"}:
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

    # ── 2. Get cart ───────────────────────────
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        if payment_method == "RAZORPAY":
            return JsonResponse({"error": "Your cart is empty."}, status=400)
        messages.error(request, "Your cart is empty.")
        return redirect("user_cart")

    summary = compute_cart_summary(cart)

    if summary["items_count"] == 0:
        if payment_method == "RAZORPAY":
            return JsonResponse({"error": "Your cart is empty."}, status=400)
        messages.error(request, "Your cart is empty.")
        return redirect("user_cart")

    # ── 3. Create order (atomic) ──────────────
    with transaction.atomic():
        cart_items = CartItem.objects.filter(cart=cart).select_related(
            "product_variant"
        )
        locked_variants = lock_variants_for_update(items=cart_items)

        try:
            validate_stock(items=cart_items, stock_lookup=locked_variants)
        except InsufficientStockError as error:
            if payment_method == "RAZORPAY":
                return JsonResponse({"error": str(error)}, status=400)
            messages.error(request, str(error))
            return redirect("user_cart")

        # ── Coupon re-validation (locked) ─────
        applied_coupon_session = request.session.get("applied_coupon")
        coupon_obj = None
        coupon_discount = Decimal("0.00")

        if applied_coupon_session:
            coupon_code = applied_coupon_session.get("code", "")
            try:
                coupon_obj, coupon_discount = validate_coupon_locked(
                    coupon_code, request.user, summary["sub_total"]
                )
            except InvalidCouponError as e:
                del request.session["applied_coupon"]
                if payment_method == "RAZORPAY":
                    return JsonResponse(
                        {"error": f"Coupon '{coupon_code}' is no longer valid: {e}"},
                        status=400,
                    )
                messages.error(
                    request, f"Coupon '{coupon_code}' is no longer valid: {e}"
                )
                return redirect(reverse("checkout") + "?step=3")

        # ── Recalculate totals ────────────────
        adjusted = recalculate_with_coupon(
            summary["sub_total"],
            summary["shipping_fee"],
            settings.GST_RATE,
            coupon_discount,
        )
        adjusted_grand_total = adjusted["grand_total"]
        adjusted_tax = adjusted["tax"]

        # ── Wallet balance check ──────────────
        if payment_method == "WALLET":
            if not can_pay_with_wallet(request.user, adjusted_grand_total):
                messages.error(
                    request,
                    "Insufficient wallet balance. Please choose another payment method.",
                )
                return redirect(reverse("checkout") + "?step=2")

        # Price lookup from cart summary
        packed_prices = {
            ci.product_variant_id: ci.product_variant.final_price
            for ci in summary["cart_items"]
        }

        # Create order record
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

        # ── RAZORPAY: shell only (no items, no stock) ──
        if payment_method == "RAZORPAY":
            order.cart_snapshot = build_cart_snapshot(
                cart_items, packed_prices, locked_variants
            )
            order.save(update_fields=["cart_snapshot"])

            txn = create_transaction(
                user=request.user,
                txn_type="ORDER_PAYMENT",
                method="RAZORPAY",
                amount=order.grand_total,
                status="PENDING",
                content_object=order,
                note=f"Razorpay payment for order {order.order_number}",
            )

            amount_paise = int(order.grand_total * 100)
            # Razorpay test mode: UPI capped at ₹1,00,000 — cap to ₹99,999
            # if settings.DEBUG:
            amount_paise = min(amount_paise, 99_999_00)
            rz_order = create_razorpay_order(amount_paise, order.order_number)
            txn.gateway_order_id = rz_order["id"]
            txn.save(update_fields=["gateway_order_id"])

        # ── COD / WALLET: full order (items + stock) ──
        else:
            for item in cart_items:
                locked_variant = locked_variants[item.product_variant_id]
                order_item = OrderItem.objects.create(
                    order=order,
                    product_variant=locked_variant,
                    quantity=item.quantity,
                    price=packed_prices.get(
                        item.product_variant_id, locked_variant.price
                    ),
                    original_price=locked_variant.price,
                )
                update_stock(
                    product_variant=locked_variant,
                    change=-item.quantity,
                    reason="ORDER_PLACED",
                    actor=request.user,
                    reference_object=order_item,
                    note=f"Order {order.order_number} placed",
                )

            if payment_method == "WALLET":
                change_order_status(order=order, to_status="CONFIRMED")
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

        # ── Common: cart + coupon cleanup ─────
        cart_items.delete()

        if coupon_obj:
            apply_coupon_to_order(coupon_obj, request.user, order)
            del request.session["applied_coupon"]

    # ── 4. Response ───────────────────────────
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
