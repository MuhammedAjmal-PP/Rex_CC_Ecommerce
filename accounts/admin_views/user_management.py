from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test

User = get_user_model()

@never_cache
@user_passes_test(lambda u:u.is_superuser,login_url="admin_login")
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
    paginator = Paginator(users, 1)
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
