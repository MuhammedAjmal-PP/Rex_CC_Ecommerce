import re
from django import forms
from django.utils import timezone

from coupons.models import Coupon


class CouponForm(forms.ModelForm):

    class Meta:
        model = Coupon
        fields = [
            "code",
            "description",
            "discount_type",
            "discount_value",
            "min_order_amount",
            "max_discount_amount",
            "usage_limit",
            "per_user_limit",
            "is_active",
            "start_date",
            "end_date",
        ]
        widgets = {
            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "E.G. SAVE20",
                    "style": "text-transform: uppercase;",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Brief description of this coupon",
                }
            ),
            "discount_type": forms.Select(
                attrs={"class": "form-control"},
            ),
            "discount_value": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 10",
                    "step": "0.01",
                }
            ),
            "min_order_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
            "max_discount_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional cap",
                    "step": "0.01",
                }
            ),
            "usage_limit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Blank = unlimited",
                }
            ),
            "per_user_limit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "1",
                }
            ),
            "is_active": forms.CheckboxInput(),
            "start_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "end_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure datetime-local inputs render correctly
        for field_name in ("start_date", "end_date"):
            if self.instance and self.instance.pk:
                val = getattr(self.instance, field_name, None)
                if val:
                    self.initial[field_name] = timezone.localtime(val).strftime(
                        "%Y-%m-%dT%H:%M"
                    )

    def clean_code(self):
        code = self.cleaned_data.get("code", "").strip().upper()
        if not code:
            raise forms.ValidationError("Coupon code is required.")
        if len(code) < 3:
            raise forms.ValidationError("Code must be at least 3 characters.")
        if not re.match(r"^[A-Z0-9\-_]+$", code):
            raise forms.ValidationError(
                "Code can only contain letters, numbers, hyphens, and underscores."
            )
        qs = Coupon.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A coupon with this code already exists.")
        return code

    def clean_discount_value(self):
        value = self.cleaned_data.get("discount_value")
        if value is not None and value <= 0:
            raise forms.ValidationError("Discount value must be greater than 0.")
        discount_type = self.cleaned_data.get("discount_type")
        if discount_type == "PERCENTAGE" and value is not None and value > 100:
            raise forms.ValidationError("Percentage discount cannot exceed 100%.")
        return value

    def clean(self):
        cleaned = super().clean()
        if (
            cleaned.get("discount_type") == "FIXED"
            and cleaned.get("discount_value")
            and cleaned.get("min_order_amount")
            and cleaned["discount_value"] >= cleaned["min_order_amount"]
        ):
            self.add_error(
                "discount_value",
                "Fixed discount must be less than the minimum order amount.",
            )
        return cleaned
