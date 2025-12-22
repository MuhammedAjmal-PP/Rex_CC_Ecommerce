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
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
