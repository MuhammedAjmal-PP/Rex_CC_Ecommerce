from django.db import models
from cloudinary.models import CloudinaryField
from django.utils.text import slugify


# Create your models here.


class Brand(models.Model):

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    tagline = models.TextField(null=True, blank=True)
    logo = CloudinaryField(
        "logo",
        null=True,
        blank=True,
        folder="brands",
        resource_type="image",
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):

        if self.pk:
            old_name = Brand.objects.values_list("name", flat=True).get(pk=self.pk)
            if old_name != self.name:
                self.slug = slugify(self.name)
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
