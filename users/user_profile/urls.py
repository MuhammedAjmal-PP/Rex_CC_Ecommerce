from django.urls import path
from .views.address_management import (
    add_address,
    address_list,
    delete_address,
    edit_address,
    toggle_default_address,
)
from .views.profile_settings import profile, edit_profile, change_password


urlpatterns = [
    # Profile
    path("profile/", profile, name="user_profile"),
    path("profile/edit/", edit_profile, name="edit_profile"),
    path("change-password/", change_password, name="change_password"),
    # Address
    path("addresses/", address_list, name="user_address"),
    path("address/add/", add_address, name="add_address"),
    path("address/<uuid:address_id>/edit/", edit_address, name="address_edit"),
    path(
        "address/<uuid:address_id>/set-default/",
        toggle_default_address,
        name="set_default_address",
    ),
    path("address/<uuid:address_id>/delete/", delete_address, name="address_delete"),
]
