from django import forms
from django.contrib.auth import get_user_model
from .models import Address
from utils.validators import (
    name_validator,
    min_len_name_validator,
    image_file_extension_validator,
    image_size_validator,
)

User = get_user_model()


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile information"""

    first_name = forms.CharField(
        validators=[min_len_name_validator, name_validator],
        max_length=100,
        required=True,
    )
    last_name = forms.CharField(
        validators=[min_len_name_validator, name_validator],
        max_length=100,
        required=False,
    )
    avatar = forms.ImageField(
        validators=[image_size_validator, image_file_extension_validator],
        required=False,
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number", "avatar"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "First Name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Last Name"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "0XXXXXXXXXX"}
            ),
            "avatar": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                    "id": "avatar-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AddressForm(forms.ModelForm):
    """Form for add and edit address of users"""

    custom_label = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g., Uncle's House, My Office",
                "id": "custom_label",
                "class": "form-control",
            }
        ),
        help_text="Enter a custom label for this address (optional)",
    )

    class Meta:

        model = Address
        fields = [
            "full_name",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "label",
            "is_default",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter Full Name",
                    "id": "full_name",
                    "class": "form-control",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "placeholder": "9090909090",
                    "id": "phone_number",
                    "type": "tel",
                    "class": "form-control",
                }
            ),
            "address_line_1": forms.TextInput(
                attrs={
                    "placeholder": "Street address, P.O. box",
                    "id": "address_line_1",
                    "class": "form-control",
                }
            ),
            "address_line_2": forms.TextInput(
                attrs={
                    "placeholder": "Apartment, suite, unit, building, floor, etc. (optional)",
                    "id": "address_line_2",
                    "class": "form-control",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "placeholder": "Enter City",
                    "id": "city",
                    "class": "form-control",
                }
            ),
            "state": forms.TextInput(
                attrs={
                    "placeholder": "Enter State",
                    "id": "state",
                    "class": "form-control",
                }
            ),
            "postal_code": forms.TextInput(
                attrs={
                    "placeholder": "Enter Postal Code",
                    "id": "postal_code",
                    "class": "form-control",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "placeholder": "Enter Country",
                    "id": "country",
                    "class": "form-control",
                }
            ),
            "label": forms.HiddenInput(
                attrs={
                    "id": "label",
                }
            ),
            "is_default": forms.CheckboxInput(
                attrs={
                    "id": "default",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            # New address: default to Home
            self.fields["label"].initial = "Home"
        else:
            # Editing existing address: check if it has a custom label
            if self.instance.label not in ["Home", "Work"]:
                # It's a custom label, populate the custom_label field
                self.initial["custom_label"] = self.instance.label

        self.fields["address_line_2"].required = False

    def clean(self):
        cleaned_data = super().clean()
        label = cleaned_data.get("label")
        custom_label = cleaned_data.get("custom_label")

        if label == "Other" and custom_label:
            cleaned_data["label"] = custom_label.strip()

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=commit)
        return instance
