from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from catalog.service import update_stock
from orders.models import Order, OrderItem
from payments.service import create_transaction
from users.cart.models import Cart, CartItem
from users.user_profile.models import Address
from users.wallet.service import (
    InsufficientBalanceError,
    WalletInactiveError,
    can_pay_with_wallet,
    debit_wallet,
)
from orders.service import (
    InsufficientStockError,
    change_order_item_status,
    change_order_status,
    lock_variants_for_update,
    validate_stock,
)


@login_required
@require_POST
def place_order_view(request):
    """
    Final order view (only COD)
    """

    address_id = request.POST.get("address_id")
    payment_method = request.POST.get("payment_method")

    if not address_id or not payment_method:
        return HttpResponseBadRequest("Invalid request")

    ALLOWED_METHODS = {"COD", "WALLET"}

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
        messages.error(request, "Your cart is empty.")
        return redirect("user_cart")

    cart_items = CartItem.objects.filter(cart=cart).select_related("product_variant")

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("user_cart")

    discount = Decimal("0")

    # Pre-check wallet balance to avoid database lock if insufficient
    if payment_method == "WALLET":
        if not can_pay_with_wallet(request.user, cart.grand_total):
            messages.error(request, "Insufficient wallet balance. Please choose another payment method.")
            return redirect(reverse("checkout") + "?step=2")

    with transaction.atomic():
        locked_variants = lock_variants_for_update(cart_items=cart_items)

        try:
            validate_stock(cart_items=cart_items, stock_lookup=locked_variants)
        except InsufficientStockError as error:
            messages.error(request, str(error))
            return redirect("user_cart")

        # 1 create the order
        order = Order.objects.create(
            user=request.user,
            billing_address=billing_address.snapshot,
            shipping_address=shipping_address.snapshot,
            sub_total=cart.sub_total,
            tax=cart.tax,
            discount=discount,
            shipping_fee=cart.shipping_fee,
            grand_total=cart.grand_total,
        )

        for item in cart_items:
            locked_variant = locked_variants[item.product_variant_id]

            # 2 create orderitems
            order_item = OrderItem.objects.create(
                order=order,
                product_variant=locked_variant,
                quantity=item.quantity,
                price=item.item_price,
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
        change_order_status(
            order=order,
            to_status="PLACED",
            note="Order placed by customer",
            actor=request.user,
        )

        # 6 Payment handling
        if payment_method == "WALLET":
            
            # Create Transaction record first
            txn = create_transaction(
                user=request.user,
                txn_type="ORDER_PAYMENT",
                method="WALLET",
                amount=order.grand_total,
                status="PAID",
                content_object=order,
                note=f"Wallet payment for order {order.order_number}",
            )
            # Debit wallet and link to Transaction
            debit_wallet(
                user=request.user,
                amount=order.grand_total,
                transaction_obj=txn,
            )
        
        else:
            # COD — record the payment transaction as PENDING
            txn = create_transaction(
                user=request.user,
                txn_type="ORDER_PAYMENT",
                method="COD",
                amount=order.grand_total,
                status="PENDING",
                content_object=order,
                note=f"COD payment for order {order.order_number}",
            )

        # Link the payment transaction to the order
        order.payment = txn
        order.save(update_fields=["payment"])

        # 7 Clear cart
        cart_items.delete()

    return redirect("order_success", order_number=order.order_number)


@login_required
@never_cache
def order_success_view(request, order_number):
    """
    Order success page
    """

    order = get_object_or_404(
        Order,
        user=request.user,
        order_number=order_number,
    )

    # Get latest order status
    current_status = order.current_status

    # Sanity check: order must be in PLACED state
    if not current_status or current_status.status != "PLACED":
        return redirect("user_order_list")

    return render(
        request,
        "orders/user/order_success.html",
        {
            "order_number": order.order_number,
        },
    )
