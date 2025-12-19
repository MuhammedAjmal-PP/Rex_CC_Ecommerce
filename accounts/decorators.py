from django.shortcuts import redirect
from functools import wraps


def superuser_only_redirect(view_func):
    """
    Decorator that redirects a superuser to the 'admin_dashboard' if they are
    authenticated. Otherwise, it executes the original view function.

    This is useful for views that should be restricted or bypassed entirely
    for administrative users (e.g., if you want to redirect them from the
    standard login or registration pages to a specific admin start page).
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the user is authenticated AND a superuser
        if request.user.is_authenticated and request.user.is_superuser:
            # If true, redirect them immediately to the admin dashboard
            return redirect("admin_dashboard")

        # If not a superuser or not authenticated, execute the original view
        return view_func(request, *args, **kwargs)

    return _wrapped_view
