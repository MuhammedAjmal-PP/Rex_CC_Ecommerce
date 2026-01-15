from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

# Create your views here.


@never_cache
@login_required(login_url="account_login")
def profile(request):
    """
    Renders the user profile dashboard.
    """
    return render(request, "user_profile/profile.html")
