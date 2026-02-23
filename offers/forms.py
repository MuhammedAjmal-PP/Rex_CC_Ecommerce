from django import forms
from django.core.exceptions import ValidationError

from offers.models import Offer


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "E.G. SUMMER SALE 10%",
            }),
            "offer_type": forms.Select(attrs={"class": "form-control", "id": "id_offer_type"}),
            "discount_type": forms.Select(attrs={"class": "form-control"}),
            "discount_value": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "E.G. 10",
                "step": "0.01",
                "min": "0",
                "max": "100",
            }),
            "start_date": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }, format="%Y-%m-%dT%H:%M"),
            "end_date": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }, format="%Y-%m-%dT%H:%M"),
            # M2M targets — render as checkbox grids in the template
            "products": forms.CheckboxSelectMultiple(),
            "categories": forms.CheckboxSelectMultiple(),
            "brands": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure datetime fields use the correct input format
        self.fields["start_date"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_date"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned_data = super().clean()
        offer_type = cleaned_data.get("offer_type")
        products = cleaned_data.get("products")
        categories = cleaned_data.get("categories")
        brands = cleaned_data.get("brands")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        discount_type = cleaned_data.get("discount_type")
        discount_value = cleaned_data.get("discount_value")

        if discount_type == "PERCENTAGE" and discount_value and discount_value > 100:
            raise ValidationError("Percentage discount cannot exceed 100%.")

        if offer_type == "PRODUCT":
            if not products:
                raise ValidationError("Product offer must have at least one product.")
            if categories or brands:
                raise ValidationError(
                    "Product offer cannot be linked to categories or brands."
                )

        elif offer_type == "CATEGORY":
            if not categories:
                raise ValidationError("Category offer must have at least one category.")
            if products or brands:
                raise ValidationError(
                    "Category offer cannot be linked to products or brands."
                )

        elif offer_type == "BRAND":
            if not brands:
                raise ValidationError("Brand offer must have at least one brand.")
            if products or categories:
                raise ValidationError(
                    "Brand offer cannot be linked to products or categories."
                )

        if start_date and end_date and start_date >= end_date:
            raise ValidationError("End date must be after start date.")

        return cleaned_data
