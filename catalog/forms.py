from django import forms
from catalog.models import Brand
from accounts.forms import alphabet_only


class BrandForm(forms.ModelForm):

    name = forms.CharField(validators=[alphabet_only])

    class Meta:
        model = Brand
        fields = ["name", "tagline", "description", "logo", "is_active"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if Brand.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A brand with this name already exists.")

        return name.title()
