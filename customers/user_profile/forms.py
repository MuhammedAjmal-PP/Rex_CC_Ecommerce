from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinLengthValidator
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
                'accept': 'image/*',
                'id': 'avatar-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make avatar not required for updates
        self.fields['avatar'].required = False


class AddressForm(forms.ModelForm):
    """Form for adding/editing addresses with comprehensive validation"""
    
    # Validators
    postal_code_validator = RegexValidator(
        regex=r'^\d{6}$',
        message='Postal code must be exactly 6 digits'
    )
    
    phone_validator = RegexValidator(
        regex=r'^\+?91?[\s-]?\d{10}$',
        message='Enter a valid 10-digit phone number (e.g., +91 9876543210 or 9876543210)'
    )
    
    name_validator = RegexValidator(
        regex=r'^[a-zA-Z\s]+$',
        message='Name should only contain letters and spaces'
    )
    
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
                'placeholder': 'Full Name',
                'maxlength': '100'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 9111111111',
                'pattern': r'^\+?91?[\s-]?\d{10}$'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'House No., Building Name, Street Address',
                'maxlength': '255'
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment, suite, unit, etc. (optional)',
                'maxlength': '255'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
                'maxlength': '100'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Province',
                'maxlength': '100'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123456',
                'pattern': r'\d{6}',
                'maxlength': '6'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country',
                'maxlength': '100'
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
        
        # Add validators
        self.fields['postal_code'].validators.append(self.postal_code_validator)
        self.fields['full_name'].validators.append(self.name_validator)
    
    def clean_phone_number(self):
        """Validate and clean phone number"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove spaces and dashes
            phone = str(phone).replace(' ', '').replace('-', '')
            # Ensure it starts with +91 or just the 10 digits
            if not phone.startswith('+91') and len(phone) == 10:
                phone = f'+91{phone}'
            elif phone.startswith('91') and len(phone) == 12:
                phone = f'+{phone}'
        return phone
    
    def clean_postal_code(self):
        """Validate postal code"""
        postal_code = self.cleaned_data.get('postal_code')
        if postal_code:
            # Remove any spaces
            postal_code = postal_code.replace(' ', '')
            if not postal_code.isdigit() or len(postal_code) != 6:
                raise forms.ValidationError('Postal code must be exactly 6 digits')
        return postal_code
    
    def clean_full_name(self):
        """Validate full name"""
        name = self.cleaned_data.get('full_name')
        if name:
            name = name.strip()
            if len(name) < 3:
                raise forms.ValidationError('Name must be at least 3 characters long')
        return name
    
    def clean_city(self):
        """Validate city name"""
        city = self.cleaned_data.get('city')
        if city:
            city = city.strip()
            if not city.replace(' ', '').isalpha():
                raise forms.ValidationError('City name should only contain letters')
        return city
    
    def clean_state(self):
        """Validate state name"""
        state = self.cleaned_data.get('state')
        if state:
            state = state.strip()
            if not state.replace(' ', '').isalpha():
                raise forms.ValidationError('State name should only contain letters')
        return state
