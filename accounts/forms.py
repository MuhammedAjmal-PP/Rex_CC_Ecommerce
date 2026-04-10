import re
from django import forms
from allauth.account.forms import SignupForm
from phonenumber_field.formfields import PhoneNumberField
from accounts.models import CustomUser


class CustomSignupForm(SignupForm):
    """Custom signup form for django-allauth with additional fields."""

    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "First Name",
                "class": "form-input",
                "autocomplete": "given-name",
            }
        ),
        label="First Name",
    )

    last_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last Name",
                "class": "form-input",
                "autocomplete": "family-name",
            }
        ),
        label="Last Name (Optional)",
    )

    phone_number = PhoneNumberField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "09876543210",
                "class": "form-input",
                "type": "tel",
                "autocomplete": "tel",
            }
        ),
        label="Phone Number (Optional)",
    )

    referral_code = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. REX-A7K3M2",
                "class": "form-input",
                "autocomplete": "off",
            }
        ),
        label="Referral Code (Optional)",
    )

    def clean_first_name(self):
        name = self.cleaned_data.get("first_name", "").strip()
        if not name:
            raise forms.ValidationError("First name is required.")
        if len(name) < 3:
            raise forms.ValidationError("Name must contain at least 3 letters.")
        if not re.match(r"^[A-Za-z]+$", name):
            raise forms.ValidationError("Only letters are allowed.")
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get("last_name", "").strip()
        if name:
            if len(name) < 3:
                raise forms.ValidationError("Name must contain at least 3 letters.")
            if not re.match(r"^[A-Za-z]+$", name):
                raise forms.ValidationError("Only letters are allowed.")
        return name

    def clean_referral_code(self):
        code = self.cleaned_data.get("referral_code", "").strip().upper()
        if not code:
            return ""
        try:
            referrer = CustomUser.objects.get(referral_code=code)
        except CustomUser.DoesNotExist:
            raise forms.ValidationError("Invalid referral code.")
        # Store the referrer for use in save()
        self._referrer = referrer
        return code

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone_number = self.cleaned_data["phone_number"]

        if hasattr(self, "_referrer"):
            user.referred_by = self._referrer

        user.save()
        return user
