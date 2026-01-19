from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from allauth.account.forms import AddEmailForm


# Create your views here.


@never_cache
@login_required(login_url="account_login")
def profile(request):
    """
    Renders the user profile dashboard.
    """
    form = PasswordChangeForm(user=request.user)
    return render(request, "user_profile/profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully")
            return redirect("user_profile")
        else:
            return render(
                request,
                "user_profile/profile.html",
                {"form": form, "show_password_modal": True},
            )

    return redirect("user_profile")
