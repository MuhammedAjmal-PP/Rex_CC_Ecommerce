from django import forms
from django.utils import timezone

from catalog.models import Brand, Category, Product
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

        # Only show active targets (exclude soft-deleted / inactive items)
        self.fields["products"].queryset = Product.objects.filter(
            is_deleted=False, is_drafted=False,
        )
        self.fields["categories"].queryset = Category.objects.filter(is_active=True)
        self.fields["brands"].queryset = Brand.objects.filter(is_active=True)

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────
    def _date_changed(self, field_name):
        """True if this is a new offer or the admin actually changed the date."""
        if not (self.instance and self.instance.pk):
            return True
        saved = Offer.objects.filter(pk=self.instance.pk).values_list(field_name, flat=True).first()
        return saved != self.cleaned_data.get(field_name)

    # ─────────────────────────────────────────────
    # Field-level validators
    # ─────────────────────────────────────────────
    def clean_name(self):
        name = self.cleaned_data.get("name", "")
        name = name.strip()
        if not name:
            raise forms.ValidationError("Offer name cannot be blank.")
        return name

    def clean_discount_value(self):
        value = self.cleaned_data.get("discount_value")
        if value is not None and value <= 0:
            raise forms.ValidationError("Discount value must be greater than 0.")
        return value

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date and self._date_changed("start_date"):
            if start_date < timezone.now():
                raise forms.ValidationError("Start date cannot be in the past.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date")
        if end_date and self._date_changed("end_date"):
            if end_date <= timezone.now():
                raise forms.ValidationError("End date must be in the future.")
        return end_date

    # ─────────────────────────────────────────────
    # Cross-field validation
    # ─────────────────────────────────────────────
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

        # ── Percentage cap ───────────────────────
        if discount_type == "PERCENTAGE" and discount_value and discount_value > 100:
            self.add_error("discount_value", "Percentage discount cannot exceed 100%.")

        # ── Date ordering ────────────────────────
        if start_date and end_date and start_date >= end_date:
            self.add_error("end_date", "End date must be after start date.")

        # ── Target exclusivity + auto-clear ──────
        if offer_type == "PRODUCT":
            if not products:
                self.add_error("products", "Product offer must have at least one product.")
            # Auto-clear stale M2M fields
            cleaned_data["categories"] = Category.objects.none()
            cleaned_data["brands"] = Brand.objects.none()

        elif offer_type == "CATEGORY":
            if not categories:
                self.add_error("categories", "Category offer must have at least one category.")
            cleaned_data["products"] = Product.objects.none()
            cleaned_data["brands"] = Brand.objects.none()

        elif offer_type == "BRAND":
            if not brands:
                self.add_error("brands", "Brand offer must have at least one brand.")
            cleaned_data["products"] = Product.objects.none()
            cleaned_data["categories"] = Category.objects.none()

        return cleaned_data