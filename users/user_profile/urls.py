from django.urls import path
from .views.address_management import (
    add_address,
    user_address,
    delete_address,
    edit_address,
    toggle_default_address,
)
from .views.profile_settings import profile, edit_profile, change_password, change_email


urlpatterns = [
    # Profile
    path("", profile, name="user_profile"),
    path("edit/", edit_profile, name="edit_profile"),
    path("change-password/", change_password, name="change_password"),
    path("change-email/", change_email, name="change_email"),
    # Address
    path("addresses/", user_address, name="user_address"),
    path("address/add/", add_address, name="add_address"),
    path("address/<uuid:address_id>/edit/", edit_address, name="address_edit"),
    path(
        "address/<uuid:address_id>/set-default/",
        toggle_default_address,
        name="set_default_address",
    ),
    path("address/<uuid:address_id>/delete/", delete_address, name="address_delete"),
]
