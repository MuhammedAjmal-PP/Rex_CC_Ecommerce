from django.urls import path
from .admin_views import (
    admin_login,
    admin_logout,
    forgot_password,
    password_reset_sent,
    reset_password,
)

urlpatterns = [
    path("login/", admin_login, name="admin_login"),
    path("logout/", admin_logout, name="admin_logout"),
    # forgot password
    path("forgot-password/", forgot_password, name="admin_forgot_password"),
    path(
        "password-reset/email-sent/",
        password_reset_sent,
        name="admin_password_reset_sent",
    ),
    path("reset-password/<str:reset_id>/", reset_password, name="admin_reset_password"),
]
