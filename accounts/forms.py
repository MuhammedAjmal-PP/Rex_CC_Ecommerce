from django import forms
from allauth.account.forms import SignupForm
from phonenumber_field.formfields import PhoneNumberField
from django.core.validators import RegexValidator


alphabet_only=RegexValidator(
    regex=r'^[a-zA-Z]+$',
    message="This field should only contain letters",
    code='invalid_alphabet'
)

class CustomSignupForm(SignupForm):
    """Custom signup form for django-allauth with additional fields."""

    first_name = forms.CharField(
        max_length=100,
        required=True,
        validators=[alphabet_only],
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
        validators=[alphabet_only],
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
                "placeholder": "+91 98765 43210",
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
    
