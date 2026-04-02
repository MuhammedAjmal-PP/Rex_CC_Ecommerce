from django.shortcuts import redirect
from django.http import Http404


class AuthFlowRedirectMiddleware:
    """
    Redirects users away from the inactive page if their account
    has been reactivated, and blocks active-only pages for inactive users.
    Handles redirects for password reset and email confirmation flows.
    """

    INACTIVE_URL = "/accounts/inactive/"
    PASSWORD_RESET_KEY_DONE_URL = "/accounts/password/reset/key/done/"
    PASSWORD_RESET_DONE_URL = "/accounts/password/reset/done/"
    CONFIRM_EMAIL_URL = "/accounts/confirm-email/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        path = request.path

        # --- Inactive page handling ---
        if path == self.INACTIVE_URL:
            if user.is_authenticated:
                if user.is_active:
                    return redirect("home")
                if not user.is_active:
                    return redirect("account_inactive")

        # --- Password reset key done (e.g. after clicking reset link) ---
        # /accounts/password/reset/key/done/
        elif path == self.PASSWORD_RESET_KEY_DONE_URL:
            if user.is_authenticated:
                return redirect("home")
            # Unauthenticated: password reset completed via key, send to login
            return redirect("account_login")

        # --- Password reset request done (e.g. "check your email" page) ---
        # /accounts/password/reset/done/
        elif path == self.PASSWORD_RESET_DONE_URL:
            if user.is_authenticated:
                return redirect("home")
            # Unauthenticated user who submitted the reset form — redirect to login
            return redirect("account_login")

        # --- Email confirmation landing page ---
        # /accounts/confirm-email/
        elif path == self.CONFIRM_EMAIL_URL:
            # Only intercept the bare listing page, not confirmation links with tokens
            if user.is_authenticated:
                return redirect("home")

        return self.get_response(request)


class BlockUnusedAllauthURLsMiddleware:
    """
    Blocks allauth URLs that are not used by the application.
    Any request to blocked paths will raise a 404 instead of
    exposing default allauth views/templates.

    Allowed allauth paths:
        - login, logout, inactive, signup
        - confirm-email (sent page + confirmation link)
        - password/reset (all reset steps)
        - google OAuth (login + token)
    """

    BLOCKED_PREFIXES = (
        "/accounts/reauthenticate/",
        "/accounts/email/",
        "/accounts/password/change/",
        "/accounts/password/set/",
        "/accounts/login/code/",
        "/accounts/3rdparty/",
        "/accounts/social/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if any(path.startswith(prefix) for prefix in self.BLOCKED_PREFIXES):
            raise Http404

        return self.get_response(request)
