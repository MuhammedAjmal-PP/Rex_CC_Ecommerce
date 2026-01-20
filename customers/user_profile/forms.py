from django import forms
from django.contrib.auth import get_user_model
from .models import Address
from allauth.account.forms import AddEmailForm

User = get_user_model()


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile information"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 XXXXXXXXXX'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make avatar not required for updates
        self.fields['avatar'].required = False


class AddressForm(forms.ModelForm):
    """Form for adding/editing addresses"""
    
    class Meta:
        model = Address
        fields = [
            'full_name', 'phone_number', 'address_line_1', 
            'address_line_2', 'city', 'state', 'postal_code', 
            'country', 'address_type', 'is_default'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 XXXXXXXXXX'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street Address'
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment, suite, etc. (optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Province'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal Code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
            'address_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make address_line_2 not required
        self.fields['address_line_2'].required = False
