from django import forms
from allauth.account.forms import SignupForm
from phonenumber_field.formfields import PhoneNumberField
from utils.validators import name_validator


class CustomSignupForm(SignupForm):
    """Custom signup form for django-allauth with additional fields."""

    first_name = forms.CharField(
        max_length=100,
        required=True,
        validators=[name_validator],
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
        validators=[name_validator],
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

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.save()
        return user
