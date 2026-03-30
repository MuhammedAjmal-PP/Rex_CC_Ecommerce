from django.shortcuts import redirect


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
