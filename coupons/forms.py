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
