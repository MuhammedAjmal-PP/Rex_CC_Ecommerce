from accounts.models import CustomUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import uuid


class Address(models.Model):
    """Users Address for shipping and billing"""

    ADDRESS_TYPE_CHOICES = [
        ("home", "Home"),
        ("work", "Work"),
        ("other", "Other"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="addresses"
    )
    full_name = models.CharField(max_length=100)
    phone_number = PhoneNumberField()
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=6)
    country = models.CharField(max_length=100, default="India")

    address_type = models.CharField(choices=ADDRESS_TYPE_CHOICES, default="home")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ["-is_default", "-created_at"]
        verbose_name_plural = "Addreeses"

    def __str__(self):
        return f"{self.user.email} - {self.full_name} - {self.city}, {self.state}"

    def save(self, *args, **kwargs):

        if self.is_default():
            Address.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        elif not Address.objects.filter(user=self.user).exclude(pk=self.pk).exists():
            self.is_default = True

        super.save(*args, **kwargs)
