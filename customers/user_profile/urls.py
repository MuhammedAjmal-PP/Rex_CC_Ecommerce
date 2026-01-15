from django.urls import path
from .views import profile, change_password

urlpatterns = [
    path("profile", profile, name="user_profile"),
    path("change-password/", change_password, name="change_password"),
]
