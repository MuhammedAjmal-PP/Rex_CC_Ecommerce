from django.urls import path
from .views.profile_settings import (
    profile,
    edit_profile,
    change_password
)


urlpatterns = [
    # Profile
    path("profile/", profile, name="user_profile"),
    path("profile/edit/", edit_profile, name="edit_profile"),
    path("change-password/", change_password, name="change_password"),
]
