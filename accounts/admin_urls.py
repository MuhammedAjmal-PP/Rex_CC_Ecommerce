from django.urls import path
from .views.admin_views.admin_auth import (
    admin_login,
    admin_logout,
    forgot_password,
    password_reset_sent,
    reset_password,
)
from .views.admin_views.user_management import (
    user_list,
    user_profile,
    user_status_toggle,
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
    # User Management
    path("users/", user_list, name="admin_users_list"),
    path("user/<int:id>/profile/", user_profile, name="admin_user_profile"),
    path(
        "user/<int:id>/toggle-status/",
        user_status_toggle,
        name="admin_user_stats_toggle",
    ),
]
