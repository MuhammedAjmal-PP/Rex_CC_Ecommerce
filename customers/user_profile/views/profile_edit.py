from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from ..models import BlockedEmail
from ..forms import ProfileEditForm

User = get_user_model()


@never_cache
@login_required(login_url="account_login")
def edit_profile(request):
    """Edit user profile (name, phone, avatar)"""
    
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("user_profile")
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, "user_profile/edit_profile.html", {"form": form})


@login_required
def change_email_request(request):
    """Handle email change requests using allauth"""
    
    if request.method == "POST":
        new_email = request.POST.get("email")
        
        if not new_email:
            messages.error(request, "Please provide a new email address.")
            return redirect("edit_profile")
        
        # Check if email is blocked
        if BlockedEmail.objects.filter(email=new_email).exists():
            messages.error(request, "This email address is not available.")
            return redirect("edit_profile")
        
        # Check if email already exists
        if User.objects.filter(email=new_email).exists():
            messages.error(request, "This email address is already in use.")
            return redirect("edit_profile")
        
        # Check if user already has this email address in their account
        if EmailAddress.objects.filter(user=request.user, email=new_email).exists():
            messages.error(request, "This email is already associated with your account.")
            return redirect("edit_profile")
        
        # Add the new email using allauth
        EmailAddress.objects.add_email(
            request, request.user, new_email, confirm=True
        )
        
        messages.success(
            request,
            f"A verification email has been sent to {new_email}. "
            "Please verify the email to complete the change."
        )
        return redirect("edit_profile")
    
    return redirect("edit_profile")


@login_required
def make_email_primary(request, email_id):
    """Make a verified email the primary email and block the old one"""
    
    email_address = get_object_or_404(
        EmailAddress, id=email_id, user=request.user, verified=True
    )
    
    # Get the old primary email
    old_primary = EmailAddress.objects.get(user=request.user, primary=True)
    old_email = old_primary.email
    
    # Block the old email
    BlockedEmail.objects.get_or_create(
        email=old_email,
        defaults={
            'original_user': request.user,
            'reason': 'Email changed by user'
        }
    )
    
    # Make the new email primary
    email_address.set_as_primary()
    
    # Update the user's email field
    request.user.email = email_address.email
    request.user.save()
    
    # Delete the old email from EmailAddress
    old_primary.delete()
    
    messages.success(request, f"Your primary email has been changed to {email_address.email}")
    return redirect("edit_profile")


@login_required
def remove_email(request, email_id):
    """Remove a non-primary email address"""
    
    email_address = get_object_or_404(
        EmailAddress, id=email_id, user=request.user, primary=False
    )
    
    email_address.delete()
    messages.success(request, "Email address removed.")
    return redirect("edit_profile")
