from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from users.user_profile.models import Address
from orders.models import Order
from users.wallet.models import Wallet, WalletTransaction
from payments.models import Transaction

User = get_user_model()


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def user_list(request):
    """
    User Managemnet View of Admin Panel , its Users list.
    """
    # Extract query parameters from request
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    try:
        page_number = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page_number = 1

    # Base queryset: all non-superuser accounts, ordered by creation date
    users = User.objects.filter(is_superuser=False).order_by("-created_at")

    # Apply search filter if query is provided
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    # Apply status filter based on user selection
    if status_filter == "active":
        users = users.filter(is_active=True)
    elif status_filter == "inactive":
        users = users.filter(is_active=False)

    # Calculate user statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    inactive_users = users.filter(is_active=False).count()

    # Paginate results (10 users per page)
    paginator = Paginator(users, 10)
    page_obj = paginator.get_page(page_number)

    # Prepare context for template rendering
    context = {
        "users": page_obj,
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "search_query": search_query,
        "status_filter": status_filter,
    }

    return render(request, "accounts/user_management/user_list.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def user_profile(request, id):
    """
    User Managemnet View of Admin Panel , its Users Profile.
    """
    user = get_object_or_404(User, id=id, is_superuser=False)

    #user addresses
    addresses = Address.objects.filter(user=user, is_active=True).order_by("-is_default", "-created_at")[:2]
    #user recent orders
    recent_orders = Order.objects.filter(user=user).order_by("-created_at")[:5]
    
    # Wallet
    wallet, _ = Wallet.objects.get_or_create(user=user)
    
    # Wallet transactions
    wallet_transactions = WalletTransaction.objects.filter(wallet__user=user).order_by("-created_at")[:5]
    
    # Overall transactions
    transactions = Transaction.objects.filter(user=user).exclude(transaction_type="REFERRAL_REWARD").order_by("-created_at")[:5]
    
    # Referral transactions
    referral_rewards = Transaction.objects.filter(user=user, transaction_type="REFERRAL_REWARD").order_by("-created_at")[:5]

    context = {
        "user": user,
        "addresses": addresses,
        "recent_orders": recent_orders,
        "wallet_balance": wallet.balance,
        "wallet_transactions": wallet_transactions,
        "transactions": transactions,
        "referral_rewards": referral_rewards,
    }

    return render(request, "accounts/user_management/user_profile.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def user_status_toggle(request, id):
    """
    Toggle active/inactive status of a user from admin panel
    """
    user = get_object_or_404(User, id=id, is_superuser=False)
    user.is_active = not user.is_active
    user.save()

    status_msg = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {status_msg} successfully.")

    return redirect(request.META.get("HTTP_REFERER", reverse("admin_users_list")))
