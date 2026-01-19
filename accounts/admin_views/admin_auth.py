from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from accounts.decorators import superuser_only_redirect
from django.contrib.auth import get_user_model
from accounts.models import PasswordReset
from django.utils import timezone
from utils.service import send_admin_password_reset_email
from django.contrib.auth.forms import SetPasswordForm


# Get User model
User = get_user_model()


# Admin login View
@never_cache
@superuser_only_redirect
def admin_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)

        if form.is_valid():
            user = form.get_user()

            if user.is_superuser:
                login(request, user)

                return redirect("admin_dashboard")

            else:
                messages.error(
                    request,
                    "You are not authorized to access the admin dashboard.",
                )
                return redirect("admin_login")
        else:
            messages.error(
                request,
                "Invalid email or password",
            )
            return redirect("admin_login")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/admin_auth/admin_login.html", {"form": form})


# Admin logout view
@never_cache
@login_required(login_url="admin_login")
def admin_logout(request):
    logout(request)
    return redirect("admin_login")


# Admin Forgot Password View
@never_cache
@superuser_only_redirect
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        request.session["reset_email"] = email

        try:
            user = User.objects.get(email=email, is_staff=True)

            PasswordReset.objects.filter(
                user__email=email,
                created_at__lt=timezone.now() - timezone.timedelta(minutes=10),
            ).delete()

            request_exists = PasswordReset.objects.filter(user__email=email).first()

            if request_exists:
                expiry_time = request_exists.created_at + timezone.timedelta(minutes=10)
                remaining_time = expiry_time - timezone.now()
                remaining_time = round(remaining_time.total_seconds() / 60)
                messages.error(
                    request,
                    f"You have already requested a password reset. Please wait {remaining_time} more minute(s) before requesting a new one.",
                )
                return redirect("admin_forgot_password")

            email_sent = send_admin_password_reset_email(user, email, request)
            if email_sent:
                return redirect("admin_password_reset_sent")
            else:
                messages.error(
                    request,
                    "Failed to send password reset email. Please try again later.",
                )
                return redirect("admin_forgot_password")

        except User.DoesNotExist:
            messages.error(request, "This email is not registered as an admin.")
            return redirect("admin_forgot_password")

    return render(request, "accounts/admin_auth/admin_forgot_password.html")


@never_cache
@superuser_only_redirect
def password_reset_sent(request):

    email = request.session.get("reset_email")

    if not email:
        messages.error(request, "Access denied. Please submit the form first.")
        return redirect("admin_forgot_password")

    request_exists = PasswordReset.objects.filter(user__email=email).exists()

    if request_exists:
        return render(request, "accounts/admin_auth/admin_password_reset_sent.html")
    else:
        messages.error(request, "You have not sent a request yet.")
        return redirect("admin_forgot_password")


@never_cache
@superuser_only_redirect
def reset_password(request, reset_id):

    session_email = request.session.get("reset_email")

    if not session_email:
        messages.error(
            request,
            "Security check failed. You must open the link on the same browser you requested it from.",
        )
        return redirect("admin_forgot_password")

    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)

        if password_reset_id.user.email != session_email:
            messages.error(request, "Unauthorized request.")
            return redirect("admin_forgot_password")

        expiry_time = password_reset_id.created_at + timezone.timedelta(minutes=10)

        if timezone.now() > expiry_time:
            password_reset_id.delete()
            messages.error(request, "Reset link has expired")
            return redirect("admin_forgot_password")

        user = password_reset_id.user

        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)

            if form.is_valid():
                form.save()
                password_reset_id.delete()
                request.session.pop("reset_email", None)
                messages.success(request, "Password reset successful.")
                return redirect("admin_login")
        else:
            form = SetPasswordForm(user)

        return render(
            request, "accounts/admin_auth/admin_reset_password.html", {"form": form}
        )

    except PasswordReset.DoesNotExist:
        messages.error(request, "Invalid link.")
        return redirect("admin_forgot_password")
