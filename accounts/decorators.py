from django.shortcuts import redirect
from functools import wraps
from django.contrib.auth.decorators import user_passes_test

# Guard: blocks non-superusers, redirects them to admin login
superuser_required = user_passes_test(
    lambda u: u.is_superuser, login_url="admin_login"
)


def superuser_only_redirect(view_func):
    """
    Bounce already-authenticated users away from admin auth pages
    (login, forgot-password, reset-password).

    - Superusers  → redirected to the admin dashboard.
    - Regular users → redirected to their profile page.
    - Unauthenticated visitors → the view executes normally.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect("admin_dashboard")
            return redirect("user_profile")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
