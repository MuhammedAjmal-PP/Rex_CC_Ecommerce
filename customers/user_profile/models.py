from django.conf import settings
from django.forms import ValidationError
from accounts.models import CustomUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import uuid
from utils.validators import (
    full_name_validator,
    min_len_name_validator,
    postal_code_validator,
)


class AddressActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Address(models.Model):
    """Users Address for shipping and billing"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="addresses"
    )
    full_name = models.CharField(
        max_length=100, validators=[full_name_validator, min_len_name_validator]
    )
    phone_number = PhoneNumberField()
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(
        max_length=6,
        validators=[postal_code_validator],
    )
    country = models.CharField(max_length=100, default="India")

    label = models.CharField(
        max_length=50,
        default="Home",
        blank=True,
        help_text="Address type: Home, Work, or custom label",
    )
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    objects = models.Manager()
    active = AddressActiveManager()

    class Meta:
        ordering = ["-is_default", "-created_at"]
        verbose_name_plural = "Addreeses"

    def __str__(self):
        return f"{self.user.email} - {self.full_name} - {self.city}, {self.state}"

    def clean(self):
        super().clean()

        if not self.user_id:
            return
        if self._state.adding:
            active_count = Address.active.filter(user=self.user).count()
            if active_count >= settings.MAX_ADDRESSES_PER_USER:
                raise ValidationError(
                    f"You can only save up to {settings.MAX_ADDRESSES_PER_USER} addresses."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        elif not Address.objects.filter(user=self.user).exclude(pk=self.pk).exists():
            self.is_default = True

        super().save(*args, **kwargs)
