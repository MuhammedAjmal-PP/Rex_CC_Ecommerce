from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from catalog.service import update_stock
from orders.models import Order, OrderItem, StatusTimeline
from users.cart.models import Cart, CartItem
from users.user_profile.models import Address
from django.contrib.contenttypes.models import ContentType


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

    if payment_method != "COD":
        return HttpResponseBadRequest("Only Cash on Delivery is supported")

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

    for item in cart_items:
        if item.quantity > item.product_variant.stock:
            messages.error(request, f"Insufficient stock for {item.product_variant}.")
            return redirect("user_cart")

    discount = Decimal("0")

    order_obj = ContentType.objects.get_for_model(Order)
    order_item_obj = ContentType.objects.get_for_model(OrderItem)

    with transaction.atomic():

        # 1 create the order
        order = Order.objects.create(
            user=request.user,
            billing_address=billing_address.snapshot,
            shipping_address=shipping_address.snapshot,
            sub_total=cart.sub_total,
            tax=cart.tax,
            discount=discount,
            shipping_fee=cart.shipping_fee,
            grant_total=cart.grand_total,
            payment_method="COD",
        )

        for item in cart_items:

            # 2 create orderitems
            order_item = OrderItem.objects.create(
                order=order,
                product_variant=item.product_variant,
                quantity=item.quantity,
                price=item.total_amount,
            )

            # 3 Initial ORDER ITEM status
            StatusTimeline.objects.create(
                content_type=order_item_obj,
                object_id=order_item.id,
                status="PENDING",
                note="Item pending fulfillment",
                actor=request.user,
            )

            # 4 update the stock and add entry to inventory log
            update_stock(
                product_variant=item.product_variant,
                change=-item.quantity,
                reason="ORDER_PLACED",
                actor=request.user,
                reference_object=order_item,
                note=f"Order {order.order_number} placed",
            )

        # 5 Initial ORDER status
        StatusTimeline.objects.create(
            content_type=order_obj,
            object_id=order.id,
            status="PLACED",
            note="Order placed by customer",
            actor=request.user,
        )

        # 6 cartitems purchased_product delete form cart
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
        return redirect("user_orders")

    return render(
        request,
        "orders/user/order_success.html",
        {
            "order_number": order.order_number,
        },
    )
