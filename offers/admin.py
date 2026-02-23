from django.contrib import admin
from offers.forms import OfferForm
from offers.models import Offer


class OfferAdmin(admin.ModelAdmin):
    form = OfferForm


admin.site.register(Offer, OfferAdmin)
