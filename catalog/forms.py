from django import forms
from catalog.models import (
    Brand,
    Category,
    Product,
    ProductVariant,
    ProductImage,
)
from accounts.forms import alphabet_only
from django.core.validators import RegexValidator

sku_validator = RegexValidator(
    regex=r"^[A-Z0-9_./-]+$",
    message="SKU can contain only uppercase letters, numbers, hyphens (-), and underscores (_).",
    code="invalid_sku",
)


class BrandForm(forms.ModelForm):

    name = forms.CharField(validators=[alphabet_only])

    class Meta:
        model = Brand
        fields = ["name", "tagline", "description", "logo", "is_active"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        brand = Brand.objects.filter(name__iexact=name)
        if self.instance.pk:
            brand = brand.exclude(pk=self.instance.pk)

        if brand.exists():
            raise forms.ValidationError("A brand with this name already exists.")

        return name.title()


class CategoryForm(forms.ModelForm):

    name = forms.CharField(validators=[alphabet_only])

    class Meta:
        model = Category
        fields = ["name", "is_active"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        category = Category.objects.filter(name__iexact=name)

        if self.instance.pk:
            category = category.exclude(pk=self.instance.pk)

        if category.exists():
            raise forms.ValidationError("A Category with this name already exists.")

        return name.title()


class ProductForm(forms.ModelForm):

    name = forms.CharField(validators=[alphabet_only])

    class Meta:
        model = Product
        fields = [
            "name",
            "brand",
            "category",
            "description",
            "thumbnail",
            "is_drafted",
        ]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        product = Product.objects.filter(name__iexact=name)

        if self.instance.pk:
            product = product.exclude(pk=self.instance.pk)

        if product.exists():
            raise forms.ValidationError("A Product with this name already exists.")

        return name.title()


class ProductVariantForm(forms.ModelForm):

    sku = forms.CharField(validators=[sku_validator])

    # Make specification fields required at the form level
    dial_color = forms.CharField(max_length=100, required=True)
    case_size_mm = forms.IntegerField(required=True, min_value=1)
    case_material = forms.CharField(max_length=100, required=True)
    movement_type = forms.CharField(max_length=100, required=True)
    strap_color = forms.CharField(max_length=100, required=True)
    strap_material = forms.CharField(max_length=100, required=True)

    class Meta:
        model = ProductVariant
        fields = [
            "product",
            "sku",
            "dial_color",
            "strap_color",
            "strap_material",
            "case_material",
            "movement_type",
            "case_size_mm",
            "price",
            "stock",
            "is_featured",
            "is_drafted",
        ]

    def clean_sku(self):
        sku = self.cleaned_data["sku"].strip()

        product_variant = ProductVariant.objects.filter(sku__iexact=sku)

        if self.instance.pk:
            product_variant = product_variant.exclude(pk=self.instance.pk)

        if product_variant.exists():
            raise forms.ValidationError(
                "A Product Variant with this sku already exists."
            )

        return sku.upper()


class ProductImageForm(forms.ModelForm):

    class Meta:
        model = ProductImage
        fields = ["image", "is_primary"]
