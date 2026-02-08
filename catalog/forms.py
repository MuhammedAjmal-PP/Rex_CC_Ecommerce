from email.policy import default
from os import name
from django import forms
from catalog.models import (
    Brand,
    Category,
    Product,
    ProductVariant,
    ProductImage,
)
from core.validators import (
    image_file_extension_validator,
    image_size_validator,
)
from django.core.validators import MaxValueValidator, MinValueValidator


class BrandForm(forms.ModelForm):

    logo = forms.ImageField(
        validators=[image_size_validator, image_file_extension_validator]
    )

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

    thumbnail = forms.ImageField(
        validators=[image_file_extension_validator, image_size_validator]
    )

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
            "discount_percentage",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make specification fields required
        required_fields = [
            "sku",
            "dial_color",
            "case_size_mm",
            "case_material",
            "movement_type",
            "strap_color",
            "strap_material",
        ]
        for field in required_fields:
            self.fields[field].required = True

        # Ensure validators from model are active (they are by default in ModelForm)
        # We can add extra widgets or attributes here if needed

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
