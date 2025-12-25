from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

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
    page_number = request.GET.get("page", 1)

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
    base_users = User.objects.filter(is_superuser=False)
    total_users = base_users.count()
    active_users = base_users.filter(is_active=True).count()
    inactive_users = base_users.filter(is_active=False).count()

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
    user = User.objects.filter(id=id).first()

    # Static data for testing
    addresses = {
        "home": {
            "name": "John Doe",
            "street": "123 Main Street",
            "apartment": "Apt 4B",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "phone": "+1 (555) 123-4567",
        },
        "office": {
            "name": "John Doe",
            "street": "456 Business Ave",
            "apartment": "Suite 200",
            "city": "Manhattan",
            "state": "NY",
            "postal_code": "10002",
            "phone": "+1 (555) 987-6543",
        },
    }

    recent_orders = [
        {
            "order_number": "#ORD-2024-001",
            "date": "Dec 20, 2024",
            "amount": 1299.99,
            "status": "delivered",
        },
        {
            "order_number": "#ORD-2024-002",
            "date": "Dec 18, 2024",
            "amount": 899.50,
            "status": "processing",
        },
        {
            "order_number": "#ORD-2024-003",
            "date": "Dec 15, 2024",
            "amount": 2499.00,
            "status": "shipped",
        },
    ]

    wallet_balance = 5420.00

    wallet_transactions = [
        {
            "type": "credit",
            "description": "Refund for Order #ORD-2024-001",
            "date": "Dec 19, 2024",
            "amount": 150.00,
        },
        {
            "type": "debit",
            "description": "Purchase - Order #ORD-2024-002",
            "date": "Dec 18, 2024",
            "amount": -899.50,
        },
        {
            "type": "credit",
            "description": "Cashback Reward",
            "date": "Dec 17, 2024",
            "amount": 50.00,
        },
    ]

    transactions = [
        {
            "type": "payment",
            "description": "Order #ORD-2024-003",
            "date": "Dec 15, 2024",
            "method": "Credit Card",
            "amount": 2499.00,
        },
        {
            "type": "refund",
            "description": "Refund - Order #ORD-2024-001",
            "date": "Dec 19, 2024",
            "method": "Wallet",
            "amount": 150.00,
        },
        {
            "type": "payment",
            "description": "Order #ORD-2024-002",
            "date": "Dec 18, 2024",
            "method": "Wallet",
            "amount": 899.50,
        },
    ]

    referral_rewards = [
        {
            "date": "Dec 10, 2024",
            "referred_user": "jane.smith@example.com",
            "amount": 25.00,
        },
        {
            "date": "Dec 5, 2024",
            "referred_user": "mike.johnson@example.com",
            "amount": 25.00,
        },
        {
            "date": "Nov 28, 2024",
            "referred_user": "sarah.williams@example.com",
            "amount": 25.00,
        },
    ]

    context = {
        "user": user,
        "addresses": addresses,
        "recent_orders": recent_orders,
        "wallet_balance": wallet_balance,
        "wallet_transactions": wallet_transactions,
        "transactions": transactions,
        "referral_rewards": referral_rewards,
    }

    return render(request, "accounts/user_management/user_profile.html", context)


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def user_status_toggle(request, id):
    """
    User Managemnet View of Admin Panel , its Users status toggle.
    """
    try:
        user = User.objects.get(id=id)
        user.is_active = not user.is_active
        user.save()

        status_msg = "activatied" if user.is_active else "deactivated"
        messages.success(request, f"User {status_msg} successfully.")

    except User.DoesNotExist:
        messages.error(request, "User Not founded")

    fallback = reverse("admin_users_list")
    previous_page = request.META.get("HTTP_REFERER", fallback)
    return redirect(previous_page)
