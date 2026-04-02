from django.urls import path
from offers.views.admin.views import offer_list, add_offer, edit_offer, delete_offer

urlpatterns = [
    path("offers/", offer_list, name="admin_offers"),
    path("offers/add/", add_offer, name="admin_offer_add"),
    path("offers/<int:pk>/edit/", edit_offer, name="admin_offer_edit"),
    path("offers/<int:pk>/delete/", delete_offer, name="admin_offer_delete"),
]
