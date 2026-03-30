from django.shortcuts import redirect
from django.http import Http404


class AccountStatusMiddleware:
    """
    Redirects users away from the inactive page if their account
    has been reactivated, and blocks active-only pages for inactive users.
    """

    INACTIVE_URL = "/accounts/inactive/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == self.INACTIVE_URL:
            user = request.user

            # Account was reactivated - redirect them out
            if user.is_authenticated:
                if user.is_active:
                    return redirect("home")

                if not user.is_active:
                    return redirect("account_inactive")

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
