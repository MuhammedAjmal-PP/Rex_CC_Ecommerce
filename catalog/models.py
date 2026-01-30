from django.db import models
from django.utils.text import slugify
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class Brand(models.Model):

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    tagline = models.TextField(null=True, blank=True)
    logo = models.ImageField(
        upload_to="brands_logo",
        blank=True,
        null=True,
        help_text="Brand Logo",
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):

        if self.pk:
            old = Brand.objects.filter(pk=self.pk).first()

            if old.name != self.name:
                self.slug = slugify(self.name)

            if old and old.logo and old.logo != self.logo:
                old.logo.delete(save=False)
        else:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):

        if self.pk:
            old_name = Category.objects.values_list("name", flat=True).get(pk=self.pk)
            if old_name != self.name:
                self.slug = slugify(self.name)
        else:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)

    brand = models.ForeignKey(
        "Brand", on_delete=models.PROTECT, related_name="products"
    )
    category = models.ManyToManyField("Category", related_name="products")

    description = models.TextField(blank=True)

    thumbnail = models.ImageField(
        upload_to="product_thumbs/",
        null=True,
        blank=True,
        help_text="Product thumbnail image",
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when product was soft deleted",
    )

    is_drafted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk:
            old = Product.objects.filter(pk=self.pk).first()
            if old.name != self.name:
                self.slug = slugify(self.name)

            if old and old.thumbnail and old.thumbnail != self.thumbnail:
                old.thumbnail.delete(save=False)
        else:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )

    sku = models.CharField(max_length=100, unique=True, db_index=True)

    dial_color = models.CharField(max_length=100, blank=True)
    strap_color = models.CharField(max_length=100, blank=True)
    strap_material = models.CharField(max_length=100, blank=True)
    case_material = models.CharField(max_length=100, blank=True)
    movement_type = models.CharField(max_length=100, blank=True)
    case_size_mm = models.PositiveIntegerField(null=True, blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text="Discount percentage (0–100)",
        null=True,
        blank=True,
    )
    stock = models.PositiveIntegerField(default=0)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when product was soft deleted",
    )

    is_featured = models.BooleanField(default=False)
    is_drafted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        ordering = ["product", "sku"]

    @property
    def discount_amount(self):
        if self.discount_percentage > 0:
            return self.price * Decimal(self.discount_percentage) / Decimal(100)
        return Decimal("0.00")

    @property
    def final_price(self):
        return self.price - self.discount_amount

    def __str__(self):
        return f"{self.product.name} ({self.sku})"


class ProductImage(models.Model):
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="images"
    )

    image = models.ImageField(
        "product_image",
        null=True,
        blank=True,
        upload_to="products_image/",
        help_text="ProductVariant Image",
    )

    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["variant"],
                condition=models.Q(is_primary=True),
                name="unique_primary_image_per_variant",
            )
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            old = ProductImage.objects.filter(pk=self.pk).first()
            if old and old.image and old.image != self.image:
                old.image.delete(save=False)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the image from Cloudinary when the model is deleted
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.variant.sku}"
