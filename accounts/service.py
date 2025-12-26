from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from .models import PasswordReset


def send_admin_password_reset_email(user, email, request):

    # Create a new password reset instance
    new_password_reset = PasswordReset(user=user)
    new_password_reset.save()

    # Create password reset URL
    password_reset_url = reverse(
        "admin_reset_password", kwargs={"reset_id": new_password_reset.reset_id}
    )
    full_password_reset_url = request.build_absolute_uri(password_reset_url)

    # Email content
    email_subject = "Admin Reset password"
    email_body = f"""
        Reset Your Admin Password

        Hello Admin,

        We received a request to reset your admin account password.

        Reset your password using the link below:
        {full_password_reset_url}

        ⏰ IMPORTANT: This link will expire in 10 minutes for security reasons.

        If you didn't request this, please ignore this email.

        ---
        This is an automated message from the Admin Panel
        """

    # Send email using send_mail
    send_mail(
        email_subject,
        email_body,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=True,
    )
