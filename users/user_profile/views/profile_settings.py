from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from users.user_profile.models import Address
from users.user_profile.forms import ProfileEditForm
from django.http import JsonResponse

User = get_user_model()


# Create your views here.


@never_cache
@login_required(login_url="account_login")
def profile(request):
    """
    profile dashboard.
    """
    return render(request, "user_profile/profile.html")


@never_cache
@login_required(login_url="account_login")
def edit_profile(request):
    """Edit user profile (name, phone, avatar)"""

    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            
            # Handle avatar removal
            if request.POST.get("remove_avatar") == "true":
                request.user.avatar.delete()
                request.user.avatar = None
                
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("user_profile")
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, "user_profile/edit_profile.html", {"form": form})


@login_required
@require_POST
def change_password(request):

    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return JsonResponse(
            {
                "success": True,
                "message": "Password changed successfully",
            }
        )

    return JsonResponse({"success": False, "errors": form.errors}, status=400)
