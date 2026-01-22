from django import forms
from django.contrib.auth import get_user_model
from utils.validators import (
    name_validator,
    name_size_validator,
    image_file_extension_validator,
    image_size_validator,
)

User = get_user_model()

class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile information"""

    first_name = forms.CharField(
        validators=[name_size_validator, name_validator], max_length=100, required=True
    )
    last_name = forms.CharField(
        validators=[name_size_validator, name_validator], max_length=100, required=False
    )
    avatar = forms.ImageField(validators=[image_size_validator,image_file_extension_validator], required=False)

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
        # Make avatar not required for updates
        self.fields["avatar"].required = False
