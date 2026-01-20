from django.urls import path
from .views.profile_settings import profile, change_password
from .views.profile_edit import (
    edit_profile,
    change_email_request,
    make_email_primary,
    remove_email,
)
from .views.address_management import (
    address_list,
    address_add,
    address_edit,
    address_delete,
    address_set_default,
)

urlpatterns = [
    # Profile
    path("profile/", profile, name="user_profile"),
    path("profile/edit/", edit_profile, name="edit_profile"),
    path("change-password/", change_password, name="change_password"),
    
    # Email management
    path("email/change/", change_email_request, name="change_email_request"),
    path("email/<int:email_id>/make-primary/", make_email_primary, name="make_email_primary"),
    path("email/<int:email_id>/remove/", remove_email, name="remove_email"),
    
    # Address management
    path("addresses/", address_list, name="address_list"),
    path("addresses/add/", address_add, name="address_add"),
    path("addresses/<uuid:address_id>/edit/", address_edit, name="address_edit"),
    path("addresses/<uuid:address_id>/delete/", address_delete, name="address_delete"),
    path("addresses/<uuid:address_id>/set-default/", address_set_default, name="address_set_default"),
]
